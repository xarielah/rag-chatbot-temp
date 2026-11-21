"""Retrieval-augmented answering: embed query (Voyage) -> search Qdrant -> ask Claude Haiku."""
from typing import cast

import anthropic
import voyageai
from anthropic.types import MessageParam

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


HISTORY_NOTE = (
    "\n\nEarlier turns of this conversation are included as chat history. The document "
    "context excerpts apply only to the latest question."
)

SUMMARY_PROMPT = (
    "You compress a conversation between a user and a document-Q&A assistant into a short "
    "running summary that will replace the older turns. Preserve the user's goals, named "
    "entities, decisions, key facts the assistant stated, and unresolved questions. Be terse. "
    "Output only the summary text."
)


def _usage(msg) -> int:
    return msg.usage.input_tokens + msg.usage.output_tokens


def _drop_leading_assistant(history: list[dict]) -> list[dict]:
    # The Messages API requires the first message to be from the user.
    i = 0
    while i < len(history) and history[i]["role"] != "user":
        i += 1
    return history[i:]


def answer(
    question: str, history: list[dict] | None = None, summary: str | None = None
) -> tuple[str, list[dict], int, int]:
    """Returns (text, sources, input_tokens, output_tokens).

    `history` is a list of {"role", "content"} holding raw question/answer text only
    (retrieved context is never persisted), oldest first.
    """
    chunks = retrieve(question)
    context = build_context(chunks) if chunks else "(no relevant documents found)"
    system = SYSTEM_PROMPT
    if history or summary:
        system += HISTORY_NOTE
    if summary:
        system += f"\n\nSummary of the earlier conversation:\n{summary}"
    messages = _drop_leading_assistant(history or []) + [
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
    ]
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    msg = client.messages.create(
        model=settings.chat_model,
        max_tokens=settings.max_tokens,
        system=system,
        messages=cast(list[MessageParam], messages),
    )
    text = "".join(b.text for b in msg.content if b.type == "text")
    sources = [
        {"source": c["source"], "page": c["page"], "score": c["score"]} for c in chunks
    ]
    return text, sources, msg.usage.input_tokens, msg.usage.output_tokens


def summarize(old_summary: str | None, messages: list[dict]) -> tuple[str, int]:
    """Fold `messages` into `old_summary`. Returns (new_summary, total_tokens_used)."""
    transcript = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
    prior = f"Existing summary:\n{old_summary}\n\n" if old_summary else ""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    msg = client.messages.create(
        model=settings.chat_model,
        max_tokens=settings.chat_summary_max_tokens,
        system=SUMMARY_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"{prior}New turns to fold in:\n{transcript}\n\nUpdated summary:",
            }
        ],
    )
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    return text, _usage(msg)
