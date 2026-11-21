"""Retrieval-augmented answering: embed query (Voyage) -> search Qdrant -> ask Claude Haiku."""
from typing import cast

import anthropic
import voyageai

from app.config import settings
from app.qdrant import get_qdrant

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions using only the provided context "
    "excerpts from the company's documents. If the context does not contain the answer, "
    "say you don't know based on the available documents. Be concise."
)


def retrieve(question: str) -> list[dict]:
    vo = voyageai.Client(api_key=settings.voyage_api_key)  # pyright: ignore[reportPrivateImportUsage]
    vector = cast(
        list[float],
        vo.embed([question], model=settings.embed_model, input_type="query").embeddings[0],
    )
    client = get_qdrant()
    if not client.collection_exists(settings.collection_name):
        return []
    hits = client.query_points(
        settings.collection_name,
        query=vector,
        limit=settings.top_k,
        score_threshold=settings.min_score,
        with_payload=True,
    ).points
    return [
        {
            "source": (h.payload or {}).get("source"),
            "page": (h.payload or {}).get("page"),
            "text": (h.payload or {}).get("text", ""),
            "score": h.score,
        }
        for h in hits
    ]


def build_context(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"[{i}] (source: {c['source']}{f', page {c['page']}' if c['page'] else ''})\n{c['text']}"
        for i, c in enumerate(chunks, 1)
    )


def answer(question: str) -> tuple[str, list[dict]]:
    chunks = retrieve(question)
    context = build_context(chunks) if chunks else "(no relevant documents found)"
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    msg = client.messages.create(
        model=settings.chat_model,
        max_tokens=settings.max_tokens,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ],
    )
    text = "".join(b.text for b in msg.content if b.type == "text")
    sources = [
        {"source": c["source"], "page": c["page"], "score": c["score"]} for c in chunks
    ]
    return text, sources
