# AUDIT

Defines what is required to produce a defensible reconstruction of any served answer.

## Audit Artifacts
| Artifact | Location | Purpose |
|----------|----------|---------|
| Bundle parquet | data/bundles/*.parquet | Immutable record of query→prompt context |
| Metadata DB | data/meta/vekbase.db | Canonical docs/chunks schema & hashes |
| Logs | stdout (ship externally) | Chronological event trace |
| Traces | OTLP backend (optional) | Latency & dependency graph |

## Bundle Schema (Target Minimal Set)
| Field | Description |
|-------|-------------|
| bundle_id | UUID v4 |
| ts | UTC timestamp |
| request_id | Correlates with logs/traces |
| query | Original user query |
| retrieval_params | k, filters, pipeline version |
| chunk_ids | Ordered list of selected chunks |
| contexts | Context texts (ordered) |
| source_paths | File origins per chunk |
| prompt_template | Template identifier |
| prompt_filled | Final prompt string |
| prompt_hash | sha256(prompt_filled) |
| model | Model used (if inference executed) |
| completion | Model output (optional if offline) |
| completion_hash | sha256(completion) |
| embedding_model | Embedding model ref |
| pipeline_version | Ingest / index pipeline version |

## Integrity Chain
1. Source file -> normalized text -> chunk hash (sha256(content))
2. Chunk IDs stable (hash of file path + offset)
3. Retrieval selects chunk_ids (logged)
4. Prompt constructed; hash stored
5. Completion hashed; optional signature (future)

## Verification Procedure (Future CLI)
```
vek audit verify --bundle <id>
  -> load bundle
  -> fetch chunk texts by id
  -> recompute hashes
  -> recompute prompt hash
  -> assert equality
```

## Minimal Logging Requirements
For each served request:
- request_id
- query
- retrieved_chunk_ids
- model/provider
- latency_ms (retrieval, llm)
- bundle_id

## Tamper Resistance (Planned)
| Measure | Description |
|---------|-------------|
| Append-only bundles | No mutation after write |
| External hash log | Periodic Merkle root over bundle hashes |
| Signature | Sign (prompt_hash, completion_hash) with private key |

## Gaps / Open Items
- No current prompt_hash stored
- No completion hash
- No verification CLI
- No Merkle roll-up

## Roadmap Priorities
1. Add prompt_hash + completion_hash to bundle writer
2. Implement verification CLI
3. Introduce periodic integrity report (JSON)
4. Optional signing layer

## Admin API Unterstützung
| Endpoint | Zweck |
|----------|------|
| GET /admin/bundles | Auflistung letzter Bundles (max 200) |
| GET /admin/bundles/verify?path=... | Basis-Validierung (Hashes falls vorhanden) |
| POST /admin/chat | Admin Chat (optional Retrieval) |

`X-Admin-Key` Header erforderlich (konfiguriert via ADMIN_API_KEY).
