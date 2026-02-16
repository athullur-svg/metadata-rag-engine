import xxhash

def stable_hash(text: str) -> str:
    """
    Deterministic hash for idempotent doc IDs / chunk IDs.
    """
    h = xxhash.xxh3_64_hexdigest(text.strip().lower())
    return h
