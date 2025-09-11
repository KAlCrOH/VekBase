from __future__ import annotations

import faiss  # type: ignore
import numpy as np


class FaissStore:
    def __init__(self, dim: int, index_path: str):
        self.dim = dim
        self.index_path = index_path
        self.index: faiss.Index | None = None

    def build_flat(self, vectors: list[list[float]], ids: list[int]):
        arr = np.array(vectors, dtype=np.float32)
        base = faiss.IndexFlatIP(self.dim)
        index = faiss.IndexIDMap2(base)
        index.add_with_ids(arr, np.array(ids, dtype=np.int64))
        self.index = index

    def save(self):
        assert self.index is not None
        faiss.write_index(self.index, self.index_path)

    def load(self):
        self.index = faiss.read_index(self.index_path)

    def search(self, query: list[float], top_k: int) -> tuple[list[int], list[float]]:
        assert self.index is not None
        q = np.array([query], dtype=np.float32)
        scores, idxs = self.index.search(q, top_k)
        return idxs[0].tolist(), scores[0].tolist()
