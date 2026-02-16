from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
import json

import numpy as np
from joblib import dump, load
from sklearn.neighbors import NearestNeighbors

from metadata_rag_engine.core.models import DocumentChunk


@dataclass
class SklearnStore:
    """
    Stable vector store using cosine similarity via sklearn NearestNeighbors.
    Works reliably on macOS (incl. Python 3.12) without native FAISS crashes.
    """
    vectors: np.ndarray
    chunks: List[DocumentChunk]
    nn: NearestNeighbors

    @staticmethod
    def build(vectors: np.ndarray, chunks: List[DocumentChunk]) -> "SklearnStore":
        if vectors.ndim != 2:
            raise ValueError("vectors must be 2D")
        nn = NearestNeighbors(metric="cosine", algorithm="auto")
        nn.fit(vectors)
        return SklearnStore(vectors=vectors, chunks=chunks, nn=nn)

    def search(self, q: np.ndarray, top_k: int) -> List[Tuple[float, DocumentChunk]]:
        if q.ndim != 2:
            raise ValueError("query vector must be 2D")
        distances, idxs = self.nn.kneighbors(q, n_neighbors=top_k)
        results: List[Tuple[float, DocumentChunk]] = []
        for dist, i in zip(distances[0].tolist(), idxs[0].tolist()):
            # cosine distance -> similarity
            sim = 1.0 - float(dist)
            results.append((sim, self.chunks[i]))
        return results

    def save(self, outdir: str) -> None:
        p = Path(outdir)
        p.mkdir(parents=True, exist_ok=True)
        dump(self.nn, p / "nn.joblib")
        np.save(p / "vectors.npy", self.vectors)
        with (p / "chunks.json").open("w", encoding="utf-8") as f:
            json.dump([c.model_dump() for c in self.chunks], f, ensure_ascii=False, indent=2)

    @staticmethod
    def load(outdir: str) -> "SklearnStore":
        p = Path(outdir)
        nn = load(p / "nn.joblib")
        vectors = np.load(p / "vectors.npy")
        chunks_raw = json.loads((p / "chunks.json").read_text(encoding="utf-8"))
        chunks = [DocumentChunk(**c) for c in chunks_raw]
        return SklearnStore(vectors=vectors, chunks=chunks, nn=nn)
