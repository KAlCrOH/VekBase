from __future__ import annotations

import hashlib


def stable_chunk_id(text: str, source: str) -> str:
    h = hashlib.sha256()
    h.update(source.encode("utf-8", errors="ignore"))
    h.update(b"\x00")
    h.update(text.encode("utf-8", errors="ignore"))
    return h.hexdigest()
