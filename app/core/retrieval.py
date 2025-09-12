# ============================================================
# Context Banner — retrieval | Category: core
# Purpose: Lokaler Keyword-basierter Retrieval Stub über Kontext-Markdown Dateien (RAG Vorbereitung, kein Netz)
# Status: Kein (ticker, as_of) Filter implementiert (siehe RAG Policy) → Backlog P1 Retrieval Filter

# Contracts
#   Inputs: retrieve(query:str, limit:int) => simple substring/occurrence scoring; list_context_files() enumeriert .md
#   Outputs: List[{'file','score','snippet'}] sortiert desc score
#   Side-Effects: File I/O=read: docs/CONTEXT/*.md; Network=none
#   Determinism: deterministic (Dateisystemzustand)

# Invariants
#   - Keine Embeddings / Kein Netzwerk
#   - Pure Keyword Count, stabile Sortierung

# Dependencies
#   Internal: docs Directory Struktur
#   External: stdlib (pathlib, typing)

# Tests
#   tests/test_retrieval.py (Smoke Keyword)

# Do-Not-Change
#   Banner policy-relevant; Änderungen nur via Task „Header aktualisieren“.
# ============================================================
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
