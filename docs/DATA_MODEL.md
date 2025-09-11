# DATA_MODEL

## Overview
Core entities enabling auditable RAG.

| Entity | Purpose | Persistence |
|--------|---------|-------------|
| Document | Source-level item (file, URL) | SQLite (documents) |
| Chunk | Retrieval unit (normalized slice of text) | SQLite (chunks) + (planned) Parquet |
| Embedding | Vector representation of chunk | FAISS index (implicit order) |
| RetrievalResult | (chunk_id, score, rank) at query time | Ephemeral (log + bundle) |
| Bundle | Query + contexts + prompt + model metadata | Parquet (bundles) |

## Document
Fields: id, source, title?, created_at (planned), content_hash (planned).

## Chunk
Fields: id, document_id, text, token_count, stable_hash (planned), version.

Stable Hash Proposal: sha256(source + 0x00 + normalized_text).

## Embedding
Not stored row-wise; FAISS index stores vectors by chunk id.

Vector Consistency Check:
- Maintain vector_dim in config
- On load, assert index dimension matches config

## Bundle
Schema (logical):
- ts (UTC ISO)
- query
- contexts: list[{id, score, source, snippet_hash?}]
- prompt: list[role, content]
- provider, model
- latency_ms? (planned)
- request_id? (planned)

## Versioning Strategy
Introduce semantic version for embedding pipeline (EMB_PIPE_VER). If changed → trigger full reindex.

## Integrity & Audit Extensions (Planned)
- Prompt hash (sha256 of concatenated messages)
- Chunk text hash in bundle for tamper detection
- Optionally sign bundle manifest (future governance)

## Parquet Layout (Planned)
`processed/chunks/date=YYYY-MM-DD/part-*.parquet`
Columns: chunk_id, document_id, source, token_count, text, hash, version.

## Open Points
- Binary artifact manifest for index (faiss checksum)
- Backfill job for adding missing hashes to legacy chunks
