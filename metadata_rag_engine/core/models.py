from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class Column(BaseModel):
    name: str
    data_type: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class Table(BaseModel):
    platform: str
    database: Optional[str] = None
    schema: Optional[str] = None  # keep for now; warning is fine
    name: str
    description: Optional[str] = None
    columns: List[Column] = Field(default_factory=list)
    properties: Dict[str, str] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    doc_id: str
    text: str
    meta: Dict[str, str] = Field(default_factory=dict)
