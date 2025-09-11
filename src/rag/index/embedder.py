from __future__ import annotations

from typing import List

from sentence_transformers import SentenceTransformer

from src.config import settings


class SBertEmbedder:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.embedding_model
        self.model = SentenceTransformer(self.model_name)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, convert_to_numpy=False, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]
