from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pathlib import Path
import glob

from src.app.api.admin_auth import require_admin
from src.app.core.config import settings
from src.app.audit.verify import verify_bundle
from src.app.rag.llm.client import LLMClient
from src.app.rag.prompt.templates import build_prompt
from src.app.rag.retrieve.retriever import Retriever

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/reindex")
def reindex(_: bool = Depends(require_admin)):
    # TODO: background task trigger placeholder
    return {"status": "accepted"}


@router.get("/bundles")
def list_bundles(_: bool = Depends(require_admin)):
    base = Path(settings.bundles_dir)
    if not base.exists():
        return {"bundles": []}
    files = sorted(glob.glob(str(base / "**" / "*.parquet"), recursive=True))
    return {"bundles": files[-200:]}  # cap


@router.get("/bundles/verify")
def verify(path: str, _: bool = Depends(require_admin)):
    return verify_bundle(path)


class ChatRequest(BaseModel):
    message: str
    retrieve: bool | None = False
    top_k: int | None = None


@router.post("/chat")
def admin_chat(req: ChatRequest, _: bool = Depends(require_admin)):
    context_text = ""
    if req.retrieve:
        r = Retriever()
        docs = r.query(req.message, req.top_k)
        context_text = "\n\n".join([d.get("text", "") for d in docs if d.get("text")])
    prompt = build_prompt(req.message, context_text)
    client = LLMClient()
    out = client.chat(prompt)
    return {"message": req.message, "context_chars": len(context_text), "output": out}
