# OBSERVABILITY

Covers logging, tracing, metrics (future), and audit coupling.

## Logging
- Library: structlog -> JSON lines
- Sink: stdout (ship via sidecar / collector)
- Enrichment Fields (current + planned):
  - ts (ISO8601)
  - level
  - event (message)
  - logger
  - request_id (planned middleware)
  - route / method
  - latency_ms
  - model / provider
  - top_k / retrieved / reranked
  - chunk_ids (array)
  - prompt_hash (planned)
  - bundle_path
  - error.type / error.msg / error.stack

### Log Events (Key)
| Event | Trigger |
|-------|---------|
| ingest.start | CLI/API ingest begins |
| ingest.file_parsed | Single file normalized/split |
| embed.batch | Embedding batch processed |
| index.write | FAISS index persisted |
| retrieve.request | Retrieval initiated |
| retrieve.result | Retrieval completed |
| rerank.result | After reranker (future) |
| prompt.built | Prompt finalized |
| llm.request | LLM call outbound |
| llm.response | LLM response received |
| bundle.written | Bundle parquet flushed |
| error | Any exception boundary |

## Tracing
- OpenTelemetry instrumentation of FastAPI + httpx
- Optional OTLP endpoint export
- Span naming:
  - HTTP /query, /ingest/trigger
  - span:retrieval
  - span:embedding.batch
  - span:llm.call
  - span:prompt.build
  - span:bundle.write
- Inject request_id into span attributes

## Metrics (Planned)
| Metric | Type | Notes |
|--------|------|-------|
| retrieval_latency_ms | histogram | P50/P95 |
| llm_latency_ms | histogram | provider tag |
| ingest_throughput_docs | counter | per minute |
| chunks_total | gauge | from DB |
| index_size | gauge | vectors count |
| errors_total | counter | by type |
| rerank_delta_mean | gauge | avg score improvement |

## Correlation Strategy
- request_id added at entry (header X-Request-ID or generated)
- Propagate in logs + spans
- Bundle metadata stores request_id + prompt_hash
- For investigations: filter logs by request_id then join to bundle parquet

## Failure Analysis Pattern
1. Identify request_id from error log
2. Pull retrieval.log lines (retrieve.request/result)
3. Inspect bundle parquet (prompt + contexts)
4. Reproduce with stored query + contexts (offline LLM) to isolate nondeterminism

## Roadmap
- Structured metrics exporter (Prometheus client)
- Log sampling for high-volume retrievals
- Spike detection alerting (error rate, latency)
