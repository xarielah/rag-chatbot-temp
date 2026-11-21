from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.qdrant import get_qdrant
from app.rag import answer

app = FastAPI(title="RAG Chatbot", docs_url="/api/docs", openapi_url="/api/openapi.json")


class HealthResponse(BaseModel):
    status: str
    qdrant: bool


@app.get("/api/health", response_model=HealthResponse)
def health():
    try:
        get_qdrant().get_collections()
        qdrant_ok = True
    except Exception:
        qdrant_ok = False
    return HealthResponse(status="ok", qdrant=qdrant_ok)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class Source(BaseModel):
    source: str | None
    page: int | None
    score: float


class ChatResponse(BaseModel):
    response: str
    sources: list[Source]


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        text, sources = answer(req.message)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Chat failed: {exc}") from exc
    return ChatResponse(response=text, sources=[Source(**s) for s in sources])
