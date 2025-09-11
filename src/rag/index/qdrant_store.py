from __future__ import annotations

from typing import Iterable, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from src.config import settings


class QdrantStore:
    def __init__(self, collection: Optional[str] = None):
        self.collection = collection or settings.vector_collection
        self.client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        self._ensure_collection()

    def _ensure_collection(self, vector_size: int = 384, distance: qmodels.Distance = qmodels.Distance.COSINE):
        try:
            self.client.get_collection(self.collection)
        except Exception:
            self.client.recreate_collection(
                collection_name=self.collection,
                vectors_config=qmodels.VectorParams(size=vector_size, distance=distance),
            )

    def upsert(self, ids: Iterable[str], vectors: List[List[float]], payloads: List[dict]):
        points = [
            qmodels.PointStruct(id=pid, vector=vec, payload=pl)
            for pid, vec, pl in zip(ids, vectors, payloads)
        ]
        self.client.upsert(collection_name=self.collection, points=points)

    def search(self, query_vector: List[float], top_k: int) -> List[qmodels.ScoredPoint]:
        res = self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
        )
        return res
