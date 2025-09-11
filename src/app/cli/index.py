from __future__ import annotations

import argparse

from src.app.core.config import settings
from src.app.rag.embed.embedder import Embedder
from src.app.rag.store.faiss_store import FaissStore
from src.app.rag.store.metadata import MetadataStore


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--vector-dim", type=int, default=settings.vector_dim)
    args = p.parse_args()

    m = MetadataStore()
    # naive: embed first N chunks (toy). In real pipeline, read from parquet to avoid DB I/O.
    # Here we just embed first 100 chunks.
    with m._conn() as c:
        rows = c.execute("SELECT id, text FROM chunks LIMIT 100").fetchall()
    ids = [int(r[0]) for r in rows]
    texts = [str(r[1]) for r in rows]

    emb = Embedder(settings.embedding_model)
    vectors = emb.embed_texts(texts)

    store = FaissStore(args.vector_dim, settings.faiss_index_path)
    store.build_flat(vectors, ids)
    store.save()
    print(f"Built FAISS index with {len(ids)} vectors -> {settings.faiss_index_path}")


if __name__ == "__main__":
    main()
