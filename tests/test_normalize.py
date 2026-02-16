from metadata_rag_engine.core.models import Table, Column
from metadata_rag_engine.core.normalize import normalize_tables

def test_normalize_creates_chunks():
    t = Table(platform="postgres", database="db", schema="public", name="users",
              columns=[Column(name="email", data_type="varchar")])
    chunks = normalize_tables([t])
    assert len(chunks) >= 2
    assert any("PII.EMAIL" in c.text for c in chunks)
