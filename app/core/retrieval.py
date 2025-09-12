"""RAG retrieval stub (local deterministic, no external calls).
Future: embed context docs + simple similarity. For now: simple keyword filter.
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Dict

DOCS_BASE = Path('docs/CONTEXT')


def list_context_files() -> List[Path]:
    if not DOCS_BASE.exists():
        return []
    return sorted([p for p in DOCS_BASE.iterdir() if p.suffix.lower() == '.md'])


def retrieve(query: str, limit: int = 3) -> List[Dict[str, str]]:
    q = query.lower().strip()
    if not q:
        return []
    hits = []
    for p in list_context_files():
        try:
            text = p.read_text(encoding='utf-8')
        except Exception:
            continue
        score = text.lower().count(q)
        if score > 0:
            snippet = ''
            idx = text.lower().find(q)
            if idx != -1:
                start = max(0, idx - 80)
                end = min(len(text), idx + 80)
                snippet = text[start:end].replace('\n', ' ')
            hits.append({'file': p.name, 'score': str(score), 'snippet': snippet})
    hits.sort(key=lambda d: int(d['score']), reverse=True)
    return hits[:limit]
