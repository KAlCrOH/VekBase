from __future__ import annotations

from typing import List, Dict

from src.config import settings
from src.rag.index.embedder import SBertEmbedder
from src.rag.index.qdrant_store import QdrantStore


class Retriever:
    def __init__(self, top_k: int | None = None):
        self.top_k = top_k or settings.top_k
        self.embedder = SBertEmbedder()
        self.store = QdrantStore()

    def query(self, user_query: str) -> List[Dict]:
        qvec = self.embedder.embed_query(user_query)
        results = self.store.search(qvec, top_k=self.top_k)
        docs: List[Dict] = []
        for sp in results:
            payload = sp.payload or {}
            payload["_score"] = sp.score
            docs.append(payload)
        return docs
