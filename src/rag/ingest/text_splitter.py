from __future__ import annotations

from typing import List

import tiktoken

from src.config import settings


def token_len(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def split_by_tokens(text: str, max_tokens: int | None = None, overlap: int = 40) -> List[str]:
    max_tokens = max_tokens or settings.max_chunk_tokens
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk = enc.decode(tokens[start:end])
        chunks.append(chunk)
        if end == len(tokens):
            break
        start = max(0, end - overlap)
    return chunks
