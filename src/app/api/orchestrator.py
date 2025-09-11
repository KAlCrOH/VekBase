from __future__ import annotations

from typing import List, Dict

from src.app.rag.retrieve.retriever import Retriever
from src.app.rag.prompt.templates import build_prompt
from src.app.rag.llm.client import LLMClient
from src.app.rag.prompt.bundler import bundle_and_write
from src.app.core.config import settings


def run_orchestration(query: str, top_k: int | None = None, do_llm: bool = False) -> Dict:
    r = Retriever()
    retrieved = r.query(query, top_k)
    contexts = [
        {"id": d["id"], "score": d["score"], "text": d.get("text", ""), "source": d.get("source")}
        for d in retrieved
    ]
    context_text = "\n\n".join([c["text"] for c in contexts if c.get("text")])
    prompt = build_prompt(query, context_text)
    output = ""
    if do_llm:
        client = LLMClient()
        output = client.chat(prompt)
    bundle_path = bundle_and_write(query, contexts, prompt, provider="openai-compatible", model=settings.openai_model)
    return {"query": query, "results": contexts, "output": output, "bundle_path": bundle_path}
