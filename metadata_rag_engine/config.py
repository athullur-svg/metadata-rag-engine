from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    app_name: str = "schemadoc-ai"
    embed_model: str = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    top_k: int = int(os.getenv("TOP_K", "6"))

settings = Settings()
