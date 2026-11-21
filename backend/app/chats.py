"""Chat persistence: history window, sliding 30-day TTL, token budget, rolling summary."""
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app import rag
from app.config import settings
from app.db import SessionLocal
from app.models import Chat, ChatMessage

log = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _expiry() -> datetime:
    return _now() + timedelta(days=settings.chat_ttl_days)


def get_chat(db: Session, user_id: uuid.UUID, chat_id: uuid.UUID) -> Chat:
    """Load a live chat owned by the user. Missing, foreign and expired all look the same (404)."""
    chat = db.execute(
        select(Chat).where(
            Chat.id == chat_id, Chat.user_id == user_id, Chat.expires_at > _now()
        )
    ).scalar_one_or_none()
    if chat is None:
        raise HTTPException(404, "Chat not found")
    return chat


def check_budget(chat: Chat | None) -> None:
    if chat is not None and chat.tokens_used >= settings.chat_token_budget:
        raise HTTPException(
            429,
            detail={
                "code": "chat_token_budget_exceeded",
                "message": "This chat reached its token limit. Start a new chat to continue.",
            },
        )


def load_history(db: Session, chat: Chat) -> list[dict]:
    """Raw messages after the summary checkpoint, capped at the last N, oldest first."""
    q = select(ChatMessage.role, ChatMessage.content).where(ChatMessage.chat_id == chat.id)
    if chat.summary_upto_message_id is not None:
        q = q.where(ChatMessage.id > chat.summary_upto_message_id)
    rows = db.execute(q.order_by(ChatMessage.id.desc()).limit(settings.chat_history_limit)).all()
    return [{"role": r.role, "content": r.content} for r in reversed(rows)]


def record_turn(
    db: Session,
    user_id: uuid.UUID,
    chat: Chat | None,
    question: str,
    answer_text: str,
    sources: list[dict],
    input_tokens: int,
    output_tokens: int,
) -> Chat:
    """Persist a completed turn atomically (both messages, token usage and TTL)."""
    if chat is None:
        chat = Chat(user_id=user_id, title=question.strip()[:60] or None, expires_at=_expiry())
        db.add(chat)
        db.flush()
    db.add(ChatMessage(chat_id=chat.id, role="user", content=question))
    db.flush()  # user message gets the lower id
    db.add(
        ChatMessage(
            chat_id=chat.id,
            role="assistant",
            content=answer_text,
            sources=sources,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
    )
    # Atomic increment so concurrent requests on one chat don't lose usage.
    db.execute(
        update(Chat)
        .where(Chat.id == chat.id)
        .values(
            tokens_used=Chat.tokens_used + input_tokens + output_tokens,
            last_message_at=func.now(),
            expires_at=_expiry(),
        )
    )
    db.commit()
    db.refresh(chat)
    return chat


def needs_summary(db: Session, chat: Chat) -> bool:
    q = select(func.count()).select_from(ChatMessage).where(
        ChatMessage.chat_id == chat.id, ChatMessage.role == "user"
    )
    if chat.summary_upto_message_id is not None:
        q = q.where(ChatMessage.id > chat.summary_upto_message_id)
    return (db.execute(q).scalar_one()) >= settings.chat_summary_every_turns


def maybe_summarize(chat_id: uuid.UUID) -> None:
    """Background task: fold messages since the checkpoint into the rolling summary.

    Opens its own DB session (the request's session is closed by then). Failures are
    logged and retried implicitly on the next turn, since the trigger condition persists.
    """
    try:
        with SessionLocal() as db:
            chat = db.get(Chat, chat_id)
            if chat is None or chat.tokens_used >= settings.chat_token_budget:
                return
            if not needs_summary(db, chat):
                return
            q = select(ChatMessage).where(ChatMessage.chat_id == chat_id)
            if chat.summary_upto_message_id is not None:
                q = q.where(ChatMessage.id > chat.summary_upto_message_id)
            msgs = db.execute(q.order_by(ChatMessage.id)).scalars().all()
            if not msgs:
                return
            old_upto = chat.summary_upto_message_id
            new_summary, tokens = rag.summarize(
                chat.summary, [{"role": m.role, "content": m.content} for m in msgs]
            )
            # Tokens were spent regardless of whether we win the checkpoint race.
            db.execute(
                update(Chat).where(Chat.id == chat_id).values(tokens_used=Chat.tokens_used + tokens)
            )
            if new_summary:
                db.execute(
                    update(Chat)
                    .where(
                        Chat.id == chat_id,
                        Chat.summary_upto_message_id.is_not_distinct_from(old_upto),
                    )
                    .values(summary=new_summary, summary_upto_message_id=msgs[-1].id)
                )
            db.commit()
    except Exception:
        log.exception("Chat summarization failed for %s", chat_id)


def purge_expired_chats() -> int:
    with SessionLocal() as db:
        res = db.execute(delete(Chat).where(Chat.expires_at <= _now()))
        db.commit()
        return res.rowcount or 0
