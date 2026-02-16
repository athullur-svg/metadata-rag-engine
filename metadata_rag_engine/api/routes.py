from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from metadata_rag_engine.core.vector_store import SklearnStore
from metadata_rag_engine.core.embedding import Embedder
from metadata_rag_engine.core.rag import RAGAssistant


router = APIRouter()


class AskRequest(BaseModel):
    question: str
    top_k: int | None = None


# Global bot instance (initialized at startup)
_bot: RAGAssistant | None = None


def initialize_bot() -> None:
    """
    Loads vector index and embedding model once at application startup.
    """
    global _bot

    index_dir = os.getenv("SCHEMADOC_INDEX", ".local/index")

    required_files = ["nn.joblib", "vectors.npy", "chunks.json"]
    missing = [
        f for f in required_files
        if not os.path.exists(os.path.join(index_dir, f))
    ]

    if missing:
        raise RuntimeError(
            f"Index not found at {index_dir}. Missing files: {missing}. "
            f"Run ingest first."
        )

    store = SklearnStore.load(index_dir)
    embedder = Embedder()
    _bot = RAGAssistant(store, embedder)


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/ask")
def ask(req: AskRequest):
    if _bot is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    return _bot.ask(req.question, req.top_k)
