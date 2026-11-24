import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app import chats
from app.auth import admin as admin_router
from app.auth import router as auth_router
from app.auth.deps import CurrentUser, get_current_user
from app.config import settings
from app.db import SessionLocal, get_db
from app.models import Chat, ChatMessage
from app.qdrant import get_qdrant
from app.rag import answer
from app.seed import seed_admins

log = logging.getLogger(__name__)


async def _purge_loop() -> None:
    # Expired chats are already invisible to reads; this just reclaims the rows.
    # Single-instance only; move to pg_cron / a scheduled job if you scale out.
    while True:
        try:
            n = await asyncio.to_thread(chats.purge_expired_chats)
            if n:
                log.info("Purged %d expired chats", n)
        except Exception:
            log.exception("Chat purge failed")
        await asyncio.sleep(3600)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        with SessionLocal() as db:
            seed_admins(db)
    except Exception:
        log.exception("Startup seeding failed (is the database migrated?)")
    purge_task = asyncio.create_task(_purge_loop())
    yield
    purge_task.cancel()


app = FastAPI(
    title="RAG Chatbot",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)
# Only used by Authlib for the short-lived OAuth state/PKCE data; the login session is DB-backed.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret or "dev-insecure-change-me",
    session_cookie="oauth_state",
    max_age=600,
    same_site="lax",
    https_only=settings.cookie_secure,
)
app.include_router(auth_router.router)
app.include_router(admin_router.router)


class HealthResponse(BaseModel):
    status: str
    qdrant: bool
    db: bool


@app.get("/api/health", response_model=HealthResponse)
def health():
    try:
        get_qdrant().get_collections()
        qdrant_ok = True
    except Exception:
        qdrant_ok = False
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return HealthResponse(status="ok", qdrant=qdrant_ok, db=db_ok)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    chat_id: uuid.UUID | None = None  # omit to start a new chat


class Source(BaseModel):
    source: str | None
    page: int | None
    score: float


class ChatResponse(BaseModel):
    response: str
    sources: list[Source]
    chat_id: uuid.UUID
    tokens_used: int
    token_budget: int


@app.post("/api/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    background: BackgroundTasks,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current.user.id
    existing = chats.get_chat(db, user_id, req.chat_id) if req.chat_id else None
    print(f"User ID: {user_id}, Chat ID: {req.chat_id}, Message: {req.message}, Existing: {existing}")
    chats.check_budget(existing)  # before any Voyage/Anthropic spend
    history = chats.load_history(db, existing) if existing else []
    try:
        reply, sources, in_tok, out_tok = answer(
            req.message, history, existing.summary if existing else None
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Chat failed: {exc}") from exc
    # Persist only after the model succeeded, so failures leave no orphan user message.
    saved = chats.record_turn(db, user_id, existing, req.message, reply, sources, in_tok, out_tok)
    if chats.needs_summary(db, saved):
        background.add_task(chats.maybe_summarize, saved.id)
    return ChatResponse(
        response=reply,
        sources=[Source(**s) for s in sources],
        chat_id=saved.id,
        tokens_used=saved.tokens_used,
        token_budget=settings.chat_token_budget,
    )


class ChatSummary(BaseModel):
    id: uuid.UUID
    title: str | None
    last_message_at: datetime
    tokens_used: int
    token_budget: int


class StoredMessage(BaseModel):
    id: int
    role: str
    content: str
    sources: list[Source] | None
    created_at: datetime


@app.get("/api/chats", response_model=list[ChatSummary])
def list_chats(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Chat)
        .where(Chat.user_id == current.user.id, Chat.expires_at > datetime.now(timezone.utc))
        .order_by(Chat.last_message_at.desc())
    ).scalars()
    return [
        ChatSummary(
            id=c.id,
            title=c.title,
            last_message_at=c.last_message_at,
            tokens_used=c.tokens_used,
            token_budget=settings.chat_token_budget,
        )
        for c in rows
    ]


@app.get("/api/chats/{chat_id}/messages", response_model=list[StoredMessage])
def chat_messages(
    chat_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chats.get_chat(db, current.user.id, chat_id)
    rows = (
        db.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_id == chat_id)
            .order_by(ChatMessage.id.desc())
            .limit(settings.chat_history_limit)
        )
        .scalars()
        .all()
    )
    return [
        StoredMessage(
            id=m.id,
            role=m.role,
            content=m.content,
            sources=[Source(**s) for s in m.sources] if m.sources else None,
            created_at=m.created_at,
        )
        for m in reversed(rows)
    ]


@app.delete("/api/chats/{chat_id}", status_code=204)
def delete_chat(
    chat_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = chats.get_chat(db, current.user.id, chat_id)
    db.delete(chat)
    db.commit()
