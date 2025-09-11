from __future__ import annotations

from src.app.core.config import settings
from src.app.rag.embed.embedder import Embedder
from src.app.rag.store.faiss_store import FaissStore
from src.app.rag.store.metadata import MetadataStore


class Retriever:
    def __init__(self):
        self.embedder = Embedder(settings.embedding_model)
        self.store = FaissStore(settings.vector_dim, settings.faiss_index_path)
        self.meta = MetadataStore()
        try:
            self.store.load()
        except Exception:
            # index not built yet
            self.store.index = None

    def query(self, text: str, top_k: int | None = None) -> list[dict]:
        if self.store.index is None:
            return []
        vec = self.embedder.embed_query(text)
        k = top_k or settings.top_k
        ids, scores = self.store.search(vec, k)
        rows = self.meta.get_chunks_with_source_by_ids(ids)
        by_id = {r["id"]: r for r in rows}
        out: list[dict] = []
        for i, s in zip(ids, scores):
            r = by_id.get(i, {"id": i})
            r["score"] = float(s)
            out.append(r)
        return out
