# ORDER_CROSSCHECK

Mapping der Orders Checklist zu Dokumentationsabdeckung.

| Order Item (Kurz) | Doc Referenz | Status |
|-------------------|--------------|--------|
| Core Config Setup | CONFIG.md | Covered |
| Logging Structlog  | OBSERVABILITY.md | Covered |
| Tracing OTel       | OBSERVABILITY.md / ARCHITECTURE.md | Covered |
| Stable Chunk IDs   | DATA_MODEL.md / INGEST.md | Covered |
| Ingest Pipeline    | INGEST.md | Covered |
| Parquet Export     | INGEST.md / ROADMAP.md | Planned |
| Embedding Module   | ARCHITECTURE.md / DATA_MODEL.md | Covered |
| FAISS Index Flat   | ARCHITECTURE.md / QUERY.md | Covered |
| IVF/HNSW Planned   | ROADMAP.md | Planned |
| Retrieval Service  | QUERY.md / ARCHITECTURE.md | Covered |
| Rerank Stage       | QUERY.md / ROADMAP.md | Planned |
| Prompt Templates   | USAGE.md / ARCHITECTURE.md | Covered |
| Bundle Writer      | AUDIT.md / USAGE.md | Covered |
| Audit Hashes       | AUDIT.md | Planned (prompt/completion)
| Verification CLI   | AUDIT.md / EVALUATION.md | Planned |
| Agents Framework   | AGENTS.md | Planned |
| Validation Agent   | AGENTS.md / EVALUATION.md | Planned |
| Safety Agent       | SECURITY.md / AGENTS.md | Planned |
| Metrics Export     | OBSERVABILITY.md | Planned |
| Request ID         | OBSERVABILITY.md | Planned |
| Security Controls  | SECURITY.md | Covered/Planned |
| Streaming Output   | QUERY.md / USAGE.md | Planned |
| Hybrid Retrieval   | QUERY.md / ROADMAP.md | Planned |
| Filters            | QUERY.md | Planned |
| Coverage Metric    | EVALUATION.md | Planned |
| Drift Monitoring   | AGENTS.md / ROADMAP.md | Planned |
| Signing Bundles    | AUDIT.md / SECURITY.md | Planned |
| CI Regression Gate | EVALUATION.md / ROADMAP.md | Planned |
| GPU Optimization   | SETUP_GPU.md / ROADMAP.md | Covered/Planned |
| Quantization       | SETUP_GPU.md / ROADMAP.md | Planned |
| Merkle Roll-up     | AUDIT.md / ROADMAP.md | Planned |
