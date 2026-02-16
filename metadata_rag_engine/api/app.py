from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

from metadata_rag_engine.api.routes import router, initialize_bot

app = FastAPI(title="Metadata RAG Engine", version="1.0.0")

@app.on_event("startup")
def _startup():
    initialize_bot()

app.include_router(router)
