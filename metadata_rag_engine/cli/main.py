from __future__ import annotations
import argparse
from pathlib import Path

from metadata_rag_engine.core.loader_datahub import DataHubJsonLoader
from metadata_rag_engine.core.normalize import normalize_tables
from metadata_rag_engine.core.embedding import Embedder
from metadata_rag_engine.core.vector_store import SklearnStore

from metadata_rag_engine.core.rag import RAGAssistant

def cmd_ingest(args) -> None:
    loader = DataHubJsonLoader()
    tables = loader.load(args.input)

    chunks = normalize_tables(tables)
    embedder = Embedder()
    vecs = embedder.embed([c.text for c in chunks])

    store = SklearnStore.build(vecs, chunks)
    store.save(args.outdir)

    print(f"✅ Indexed {len(chunks)} chunks into {args.outdir}")


def cmd_ask(args) -> None:
    store = SklearnStore.load(args.index)
    embedder = Embedder()
    bot = RAGAssistant(store, embedder)
    resp = bot.ask(args.q)
    print(resp["answer"])

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="schemadoc-ai")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_ing = sub.add_parser("ingest", help="Ingest metadata JSON and build vector index")
    p_ing.add_argument("--input", required=True)
    p_ing.add_argument("--outdir", required=True)
    p_ing.set_defaults(func=cmd_ingest)

    p_ask = sub.add_parser("ask", help="Ask questions against an index")
    p_ask.add_argument("--index", required=True)
    p_ask.add_argument("--q", required=True)
    p_ask.set_defaults(func=cmd_ask)
    return p

def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
