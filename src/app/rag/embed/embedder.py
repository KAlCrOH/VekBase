from __future__ import annotations

from typing import Iterable

import torch
from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self, model_name: str, device: str | None = None):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = SentenceTransformer(model_name, device=self.device)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vecs = self.model.encode(texts, batch_size=64, convert_to_numpy=False, normalize_embeddings=True)
        return [v.tolist() for v in vecs]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]
