from fastapi import FastAPI
from pydantic import BaseModel
from qdrant_client import QdrantClient
from app.config import settings

app = FastAPI(title="RAG Chatbot", docs_url="/api/docs", openapi_url="/api/openapi.json")

class HealthResponse(BaseModel):
    status: str
    qdrant: bool

@app.get("/api/health", response_model=HealthResponse)
def health():
    try:
        QdrantClient(url=settings.qdrant_url).get_collections()
        qdrant_ok = True
    except Exception:
        qdrant_ok = False
    return HealthResponse(status="ok", qdrant=qdrant_ok)