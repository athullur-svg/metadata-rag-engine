from __future__ import annotations

from typing import Dict, Any, List, Tuple

from metadata_rag_engine.config import settings
from metadata_rag_engine.core.embedding import Embedder
from metadata_rag_engine.core.vector_store import SklearnStore


def _build_ref(
    platform: str = "",
    database: str = "",
    schema: str = "",
    table: str = "",
    column: str = "",
) -> str:
    """
    Build a clean reference string like:
      postgres:finance.public.customers.customer_id
    Handles missing parts without leaving trailing dots.
    """
    base_parts = [p for p in [database, schema, table] if p]
    base = ".".join(base_parts)
    ref = f"{platform}:{base}" if platform else base

    if column:
        ref = f"{ref}.{column}" if ref else column

    # Final cleanup (just in case)
    return ref.replace("..", ".").strip(".")


class RAGAssistant:
    def __init__(self, store: SklearnStore, embedder: Embedder):
        self.store = store
        self.embedder = embedder

    def ask(self, question: str, top_k: int | None = None) -> Dict[str, Any]:
        k = top_k or settings.top_k

        qv = self.embedder.embed([question])
        hits: List[Tuple[float, Any]] = self.store.search(qv, k)

        assets = []
        pii_refs = []

        for score, chunk in hits:
            meta = chunk.meta or {}
            assets.append(
                {
                    "score": round(float(score), 4),
                    "level": meta.get("level", ""),
                    "platform": meta.get("platform", ""),
                    "database": meta.get("database", ""),
                    "schema": meta.get("schema", ""),
                    "table": meta.get("table", ""),
                    "column": meta.get("column", ""),
                }
            )
            if "PII." in (chunk.text or ""):
                pii_refs.append(meta)

        answer_lines = [f"Top matches for: {question}"]

        for a in assets[: min(5, len(assets))]:
            ref = _build_ref(
                platform=a.get("platform", ""),
                database=a.get("database", ""),
                schema=a.get("schema", ""),
                table=a.get("table", ""),
                column=a.get("column", ""),
            )
            answer_lines.append(f"- {ref} (score={a['score']})")

        if pii_refs:
            answer_lines.append("\nPII signals found (heuristic):")
            for m in pii_refs[:5]:
                ref = _build_ref(
                    platform=m.get("platform", ""),
                    database=m.get("database", ""),
                    schema=m.get("schema", ""),
                    table=m.get("table", ""),
                    column=m.get("column", ""),
                )
                answer_lines.append(f"- {ref}")

        return {
            "question": question,
            "answer": "\n".join(answer_lines),
            "matches": assets,
        }
