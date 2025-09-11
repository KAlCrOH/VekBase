# CONFIG

Central configuration handled by `config.py` via environment variables.

## Core Variables
| Variable | Default | Description |
|----------|---------|-------------|
| VECTOR_DIM | 768 | Embedding dimension (must match model) |
| FAISS_INDEX_PATH | ./data/index/faiss/index.bin | Path to FAISS index file |
| SQLITE_PATH | ./data/meta/vekbase.db | Metadata DB path |
| PARQUET_DIR | ./data/processed | Planned chunk parquet output |
| BUNDLES_DIR | ./data/bundles | Bundle parquet output |
| EMBEDDING_MODEL | BAAI/bge-base-en-v1.5 | Dense model name |
| OPENAI_BASE_URL | http://localhost:11434/v1 | OpenAI-compatible endpoint |
| OPENAI_API_KEY | local-ollama | API key (dummy for local) |
| OPENAI_MODEL | llama3.1 | Chat model name |
| TOP_K | 5 | Default retrieval depth |
| MAX_CHUNK_TOKENS | 350 | Chunk size cap |
| LOG_LEVEL | INFO | Logging verbosity |
| OTEL_EXPORTER_OTLP_ENDPOINT | (empty) | Enable tracing export if set |

## Advanced / Planned
| Variable | Purpose |
|----------|---------|
| ENABLE_RERANK | Toggle reranking stage |
| INDEX_TYPE | flat, ivf, hnsw (future) |
| IVF_LISTS | IVF coarse quantizer size |
| HNSW_M | Graph M parameter |
| RERANK_MODEL | Cross-encoder name |
| EMB_BATCH_SIZE | Override embedding batch size |
| EMB_PIPE_VER | Pipeline version for reindex triggers |

## Configuration Principles
- Single source: no duplicated constants
- Fail fast: mismatch (e.g., index dim) should raise
- Determinism: stable ids enable idempotent pipelines
