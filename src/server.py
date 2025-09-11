from __future__ import annotations

import logging
from fastapi import FastAPI

from src.app.core.logging import setup_logging
from src.app.core.tracing import setup_tracing, instrument_fastapi
from src.app.api.routes_query import router as query_router
from src.app.api.routes_ingest import router as ingest_router
from src.app.api.routes_admin import router as admin_router


def create_app() -> FastAPI:
    setup_logging()
    setup_tracing()
    app = FastAPI(title="VekBase RAG API", version="0.1.0")
    instrument_fastapi(app)
    app.include_router(query_router)
    app.include_router(ingest_router)
    app.include_router(admin_router)
    return app


app = create_app()
