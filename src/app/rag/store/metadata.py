from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from src.app.core.config import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  title TEXT
);

CREATE TABLE IF NOT EXISTS chunks(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  document_id INTEGER NOT NULL,
  text TEXT NOT NULL,
  token_count INTEGER NOT NULL,
  FOREIGN KEY(document_id) REFERENCES documents(id)
);
"""


@dataclass
class Chunk:
    id: int
    document_id: int
    text: str
    token_count: int


class MetadataStore:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.sqlite_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._ensure()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _ensure(self):
        with self._conn() as c:
            c.executescript(SCHEMA)

    def insert_document(self, source: str, title: str | None = None) -> int:
        with self._conn() as c:
            cur = c.execute("INSERT INTO documents(source, title) VALUES (?, ?)", (source, title))
            return int(cur.lastrowid)

    def insert_chunks(self, document_id: int, chunks: list[tuple[str, int]]) -> list[int]:
        with self._conn() as c:
            cur = c.executemany(
                "INSERT INTO chunks(document_id, text, token_count) VALUES (?, ?, ?)",
                [(document_id, t, n) for (t, n) in chunks],
            )
            # sqlite3 executemany lastrowid is unreliable; we don't need ids back now
            return []

    def get_chunk_texts_by_ids(self, ids: list[int]) -> list[str]:
        if not ids:
            return []
        q = f"SELECT id, text FROM chunks WHERE id IN ({','.join('?'*len(ids))})"
        with self._conn() as c:
            rows = c.execute(q, ids).fetchall()
        id_to_text = {int(r[0]): str(r[1]) for r in rows}
        return [id_to_text.get(i, "") for i in ids]

    def get_chunks_with_source_by_ids(self, ids: list[int]) -> list[dict]:
        if not ids:
            return []
        ph = ','.join('?' * len(ids))
        q = f"""
        SELECT c.id, c.text, c.token_count, d.source
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE c.id IN ({ph})
        """
        with self._conn() as c:
            rows = c.execute(q, ids).fetchall()
        data = []
        for r in rows:
            data.append({
                "id": int(r[0]),
                "text": str(r[1]),
                "token_count": int(r[2]),
                "source": str(r[3]) if r[3] is not None else None,
            })
        # preserve order
        by_id = {d["id"]: d for d in data}
        return [by_id.get(i, {"id": i}) for i in ids]
