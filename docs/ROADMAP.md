# ROADMAP

High-level phased delivery aligned with auditability + performance goals.

## Phase 0 (Current - Scaffold)
- Core ingest (txt)
- FAISS flat index
- Basic retrieval + prompt + bundle
- OpenAI-compatible LLM call
- Architecture & data model docs

## Phase 1 (Integrity & Observability)
- prompt_hash + completion_hash in bundles
- request_id middleware
- Metrics (Prometheus client)
- Rerank stub wiring (feature flag)
- Verification CLI (hash check)

## Phase 2 (Quality & Scale)
- Parquet chunk store export
- Full batch index (remove LIMIT 100)
- IVF / HNSW index options
- ReRankAgent with cross-encoder
- Streaming responses
- Hybrid retrieval (BM25 + dense)

## Phase 3 (Security & Agents)
- Rate limiting + auth key middleware
- SafetyAgent (PII regex)
- ValidationAgent (context coverage score)
- Chunk hash verification on retrieval
- Signed bundles (optional)

## Phase 4 (Advanced Ops)
- Drift monitoring on embeddings
- Adaptive chunking (token budget aware)
- Event bus (Redis Streams) + dashboard
- Merkle roll-up of bundle hashes

## Phase 5 (Optimization & Expansion)
- GPU FAISS (flat + IVF) automatic selection
- Quantization (INT8) for large indexes
- Knowledge freshness scoring (temporal decay)
- Multi-tenant namespace isolation

## Success Metrics
| Dimension | KPI |
|----------|-----|
| Retrieval Quality | >=10% MRR lift after rerank |
| Latency | P95 < 1s retrieval (local) |
| Integrity | 100% bundle verification pass |
| Observability | <5% logs without request_id |
| Security | 0 critical findings in quarterly scan |

## Exit Criteria per Phase
- Phase 1: All audit hashes + metrics exported
- Phase 2: Hybrid retrieval behind flag stable
- Phase 3: Agents integrated with <15% latency overhead
- Phase 4: Drift alerts actionable (false positive <10%)

## Risk Register (Active)
| Risk | Mitigation |
|------|------------|
| Index drift | Pipeline version gating |
| Latency regression | Benchmark CI gate |
| Prompt injection | Strict template & validation agent |
| Data poisoning | Quarantine + hash scan pre-index |
