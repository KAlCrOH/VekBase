from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.rag.query.retriever import Retriever

app = FastAPI(title="VekBase RAG API")
retriever = Retriever()


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = None


class QueryResponse(BaseModel):
    query: str
    results: List[dict]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    try:
        r = Retriever(top_k=req.top_k) if req.top_k else retriever
        results = r.query(req.query)
        return QueryResponse(query=req.query, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
