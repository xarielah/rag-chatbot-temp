"""Ingest documents from DOCS_DIR into Qdrant.

Idempotent: unchanged files are skipped, changed files are re-embedded,
and --prune removes vectors of files that no longer exist.
"""
import argparse
import hashlib
import sys
import uuid
from collections import Counter
from pathlib import Path
from typing import cast

import voyageai
from pypdf import PdfReader
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from app.config import settings
from app.qdrant import get_qdrant

SUPPORTED = {".md", ".txt", ".pdf"}
EMBED_BATCH = 64
COLLECTION = settings.collection_name


def extract_pages(path: Path) -> list[tuple[int | None, str]]:
    """Returns (page number, text) pairs. Non-PDF files are a single page with no number."""
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(path)
        return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]
    return [(None, path.read_text(encoding="utf-8", errors="ignore"))]


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    text = " ".join(text.split())
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start : start + size])
        if start + size >= len(text):
            break
        start += size - overlap
    return chunks


def make_chunks(path: Path) -> list[dict]:
    return [
        {"text": piece, "page": page}
        for page, text in extract_pages(path)
        for piece in chunk_text(text, settings.chunk_size, settings.chunk_overlap)
    ]


def embed_documents(texts: list[str]) -> list[list[float]]:
    vo = voyageai.Client(api_key=settings.voyage_api_key) # pyright: ignore[reportPrivateImportUsage]
    vectors: list[list[float]] = []
    for i in range(0, len(texts), EMBED_BATCH):
        result = vo.embed(texts[i : i + EMBED_BATCH], model=settings.embed_model, input_type="document")
        vectors.extend(cast(list[list[float]], result.embeddings))
    return vectors


def by_source(source: str) -> Filter:
    return Filter(must=[FieldCondition(key="source", match=MatchValue(value=source))])


def ensure_collection(client: QdrantClient, vector_size: int) -> None:
    if client.collection_exists(COLLECTION):
        return
    client.create_collection(
        COLLECTION, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
    )
    client.create_payload_index(COLLECTION, field_name="source", field_schema=PayloadSchemaType.KEYWORD)


def ingest_file(client: QdrantClient, path: Path, docs_dir: Path, embed=embed_documents) -> str:
    source = path.relative_to(docs_dir).as_posix()
    file_hash = hashlib.sha256(path.read_bytes()).hexdigest()

    existing = []
    if client.collection_exists(COLLECTION):
        existing, _ = client.scroll(
            COLLECTION, scroll_filter=by_source(source), limit=1, with_payload=["file_hash"]
        )
    if existing and (existing[0].payload or {}).get("file_hash") == file_hash:
        return "skipped"

    chunks = make_chunks(path)
    if not chunks:
        if existing:
            client.delete(COLLECTION, points_selector=FilterSelector(filter=by_source(source)))
        return "empty"

    vectors = embed([c["text"] for c in chunks])   # embed first, so the old version stays searchable meanwhile
    ensure_collection(client, len(vectors[0]))
    if existing:
        client.delete(COLLECTION, points_selector=FilterSelector(filter=by_source(source)))

    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source}#{i}")),
            vector=vector,
            payload={
                "source": source,
                "page": chunk["page"],
                "chunk_index": i,
                "file_hash": file_hash,
                "text": chunk["text"],
            },
        )
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]
    client.upsert(COLLECTION, points=points)
    return "updated" if existing else "added"


def prune(client: QdrantClient, keep: set[str]) -> int:
    if not client.collection_exists(COLLECTION):
        return 0
    stale: set[str] = set()
    offset = None
    while True:
        points, offset = client.scroll(COLLECTION, limit=256, offset=offset, with_payload=["source"])
        stale.update(
            p.payload["source"]
            for p in points
            if p.payload is not None and p.payload["source"] not in keep
        )
        if offset is None:
            break
    for source in stale:
        client.delete(COLLECTION, points_selector=FilterSelector(filter=by_source(source)))
    return len(stale)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest documents into Qdrant")
    parser.add_argument("--prune", action="store_true", help="remove vectors of files that no longer exist")
    args = parser.parse_args()

    docs_dir = Path(settings.docs_dir)
    if not docs_dir.is_dir():
        sys.exit(f"Docs folder not found: {docs_dir}")

    client = get_qdrant()
    files = sorted(p for p in docs_dir.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED)
    stats: Counter = Counter()
    for path in files:
        status = ingest_file(client, path, docs_dir)
        stats[status] += 1
        print(f"{status:8} {path.relative_to(docs_dir)}")

    if args.prune:
        stats["removed"] = prune(client, {p.relative_to(docs_dir).as_posix() for p in files})

    print("summary:", dict(stats))


if __name__ == "__main__":
    main()