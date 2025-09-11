from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from src.app.core.logging import get_logger
from src.app.api.orchestrator import run_orchestration

router = APIRouter()
log = get_logger(__name__)


class QueryRequest(BaseModel):
    query: str
    top_k: int | None = None


class QueryResponse(BaseModel):
    query: str
    results: list[dict]


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest):
    log.info("query_received", query=req.query, top_k=req.top_k)
    result = run_orchestration(req.query, req.top_k, do_llm=False)
    return QueryResponse(query=req.query, results=result["results"]) 
