from __future__ import annotations
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

from metadata_rag_engine.config import settings

class Embedder:
    def __init__(self, model_name: str | None = None):
        self.model = SentenceTransformer(model_name or settings.embed_model)

    def embed(self, texts: List[str]) -> np.ndarray:
        vecs = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vecs, dtype="float32")
