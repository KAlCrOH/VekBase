from __future__ import annotations

from pydantic import BaseModel
import os


class Settings(BaseModel):
    vector_dim: int = int(os.getenv("VECTOR_DIM", "768"))
    faiss_index_path: str = os.getenv("FAISS_INDEX_PATH", "./data/index/faiss/index.bin")
    sqlite_path: str = os.getenv("SQLITE_PATH", "./data/meta/vekbase.db")
    parquet_dir: str = os.getenv("PARQUET_DIR", "./data/processed")
    bundles_dir: str = os.getenv("BUNDLES_DIR", "./data/bundles")

    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")

    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "local-ollama")
    openai_model: str = os.getenv("OPENAI_MODEL", "llama3.1")

    top_k: int = int(os.getenv("TOP_K", "5"))
    max_chunk_tokens: int = int(os.getenv("MAX_CHUNK_TOKENS", "350"))

    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    otlp_endpoint: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    admin_api_key: str = os.getenv("ADMIN_API_KEY", "")


settings = Settings()
