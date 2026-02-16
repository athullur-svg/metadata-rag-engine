from __future__ import annotations
from typing import List, Tuple
import re

from metadata_rag_engine.core.models import Table, DocumentChunk
from metadata_rag_engine.core.hashing import stable_hash

PII_PATTERNS = [
    (re.compile(r"\b(email|e_mail)\b", re.I), "PII.EMAIL"),
    (re.compile(r"\b(phone|mobile|tel)\b", re.I), "PII.PHONE"),
    (re.compile(r"\b(ssn|social_security)\b", re.I), "PII.SSN"),
    (re.compile(r"\b(dob|date_of_birth)\b", re.I), "PII.DOB"),
    (re.compile(r"\b(card|pan|cc_num)\b", re.I), "PII.CARD"),
]

def infer_tags(col_name: str) -> List[str]:
    tags: List[str] = []
    for pat, tag in PII_PATTERNS:
        if pat.search(col_name):
            tags.append(tag)
    return tags

def table_to_chunks(t: Table) -> List[DocumentChunk]:
    """
    Turn one Table into multiple searchable chunks:
    - table chunk
    - column chunks
    """
    chunks: List[DocumentChunk] = []

    table_id = stable_hash(f"{t.platform}|{t.database}|{t.schema}|{t.name}")
    header = f"DATASET {t.platform}:{t.database}.{t.schema}.{t.name}".replace("None.", "").replace(".None", "")
    table_text = header + "\n"

    if t.description:
        table_text += f"Description: {t.description}\n"
    if t.properties:
        table_text += "Properties:\n" + "\n".join([f"- {k}: {v}" for k, v in t.properties.items()]) + "\n"

    col_lines = []
    for c in t.columns:
        auto_tags = infer_tags(c.name)
        merged_tags = sorted(set((c.tags or []) + auto_tags))
        col_lines.append(f"- {c.name} ({c.data_type or 'unknown'}) tags={merged_tags}")

    if col_lines:
        table_text += "Columns:\n" + "\n".join(col_lines)

    chunks.append(DocumentChunk(doc_id=table_id, text=table_text, meta={
        "level": "table",
        "platform": t.platform,
        "database": t.database or "",
        "schema": t.schema or "",
        "table": t.name,
    }))

    # Column chunks for precision search
    for c in t.columns:
        auto_tags = infer_tags(c.name)
        merged_tags = sorted(set((c.tags or []) + auto_tags))
        col_id = stable_hash(f"{table_id}|col|{c.name}")
        col_text = (
            f"{header}\n"
            f"COLUMN {c.name}\n"
            f"Type: {c.data_type or 'unknown'}\n"
            f"Tags: {merged_tags}\n"
            f"Description: {c.description or 'N/A'}"
        )
        chunks.append(DocumentChunk(doc_id=col_id, text=col_text, meta={
            "level": "column",
            "platform": t.platform,
            "database": t.database or "",
            "schema": t.schema or "",
            "table": t.name,
            "column": c.name,
        }))

    return chunks

def normalize_tables(tables: List[Table]) -> List[DocumentChunk]:
    out: List[DocumentChunk] = []
    for t in tables:
        out.extend(table_to_chunks(t))
    return out
