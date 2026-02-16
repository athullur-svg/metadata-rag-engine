from metadata_rag_engine.core.hashing import stable_hash

def test_stable_hash_deterministic():
    a = stable_hash("Hello")
    b = stable_hash(" hello ")
    assert a == b
