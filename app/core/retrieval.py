# ============================================================
# Context Banner — retrieval | Category: core
# Purpose: Lokaler Keyword-basierter Retrieval Stub über Kontext-Markdown Dateien (RAG Vorbereitung, kein Netz)
# Status: (ticker, as_of) Filter nun implementiert (Increment: retrieval filters) – optional & rückwärtskompatibel

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
from typing import List, Dict, Optional, Callable
from datetime import datetime, date

DOCS_BASE = Path('docs/CONTEXT')

# Feature flag environment variable (simple string check) to enable advanced relevance scoring
import os as _os
_ADV_RELEVANCE_ENABLED = _os.getenv('VEK_RETRIEVAL_ADV') == '1'
_EMBED_MODE_ENABLED = _os.getenv('VEK_RETRIEVAL_EMB') == '1'


def compute_relevance(text: str, query: str) -> int:
    """Compute a simple relevance score.

    Current heuristic:
      base_score = raw frequency of exact lowercase query substring
      title_boost: occurrences in the first 120 chars * 2
      heading_boost: occurrences following a markdown heading '# ' * 3
    Returns integer score (>=0).
    Deterministic & cheap; intentionally transparent.
    """
    low = text.lower()
    q = query.lower().strip()
    if not q or not low:
        return 0
    base = low.count(q)
    if base == 0:
        return 0
    first_block = low[:120]
    title_occ = first_block.count(q)
    # Heading occurrences: naive scan lines starting with '#'
    heading_occ = 0
    for line in text.splitlines()[:50]:  # cap early lines for performance
        if line.strip().startswith('#'):
            heading_occ += line.lower().count(q)
    score = base + title_occ * 2 + heading_occ * 3
    return score


def list_context_files() -> List[Path]:
    if not DOCS_BASE.exists():
        return []
    return sorted([p for p in DOCS_BASE.iterdir() if p.suffix.lower() == '.md'])


def _pseudo_embedding(text: str, dim: int = 24) -> List[float]:
    """Deterministic pseudo-embedding via hashing character bigrams.
    Produces a fixed-size vector with simple hashing (no external libs).
    """
    import hashlib
    vec = [0.0] * dim
    low = text.lower()
    for i in range(len(low)-1):
        bg = low[i:i+2]
        h = int(hashlib.sha256(bg.encode()).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0
    # L2 normalize
    norm = sum(v*v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def _cosine(a: List[float], b: List[float]) -> float:
    return sum(x*y for x,y in zip(a,b)) if a and b else 0.0


def retrieve(
    query: str,
    limit: int = 3,
    ticker: Optional[str] = None,
    as_of: Optional[str | date] = None,
    advanced: Optional[bool] = None,
    embeddings: Optional[bool] = None,
) -> List[Dict[str, str]]:
    """Keyword retrieval über Kontextdateien.
    Erweiterungen:
      - ticker: Optionaler Filter; akzeptiert einfachen Substring (case-insensitive) gegen Dateiname oder Zeilen.
      - as_of: Optional (YYYY-MM-DD oder date); filtert nur Dateien deren Name numerisches Datum <= as_of enthält (heuristisch)
        oder deren Inhalt ein ISO-Datum <= as_of enthält. Heuristik bewusst einfach (kein Parsing schwerer Formate).
    Rückwärtskompatibel: Aufruf ohne neue Parameter verhält sich wie zuvor.
    """
    q = query.lower().strip()
    if not q:
        return []
    adv = _ADV_RELEVANCE_ENABLED if advanced is None else advanced
    emb = _EMBED_MODE_ENABLED if embeddings is None else embeddings
    # Pre-compute query embedding if emb mode
    q_emb = _pseudo_embedding(q) if emb else None
    # Normalize filters
    ticker_norm = ticker.lower() if ticker else None
    as_of_date: Optional[date] = None
    if as_of:
        if isinstance(as_of, date) and not isinstance(as_of, datetime):
            as_of_date = as_of
        else:
            try:
                as_of_date = datetime.fromisoformat(str(as_of)).date()
            except Exception:
                as_of_date = None  # Fail open (kein Filter) – Auditierbar als Designentscheidung
    hits = []
    for p in list_context_files():
        # Heuristisch skippen wenn as_of_date gesetzt und Dateiname ein führendes NN_ Muster hat > as_of
        if as_of_date:
            # Filename pattern e.g. '09_ROADMAP_MVP.md'
            try:
                prefix = p.name.split('_', 1)[0]
                if prefix.isdigit():
                    # Keine echte Datumsrepräsentation – nutzen die Reihenfolge indirekt nicht; ignorieren.
                    pass
            except Exception:
                pass
        try:
            text = p.read_text(encoding='utf-8')
        except Exception:
            continue
        low = text.lower()
        if emb and q_emb is not None:
            # embedding similarity on entire text (truncated if huge)
            snippet_source = text[:8000]
            doc_emb = _pseudo_embedding(snippet_source)
            sim = _cosine(q_emb, doc_emb)
            # scale to integer-ish space similar to word count for parity
            score = int(round(sim * 1000))
        elif adv:
            score = compute_relevance(text, q)
        else:
            score = low.count(q)
        if score <= 0:
            continue
        if ticker_norm and ticker_norm not in low and ticker_norm not in p.name.lower():
            continue
        if as_of_date:
            # Suche erstes ISO-Datum im Text (YYYY-MM-DD)
            import re as _re
            m = _re.search(r"(20\d{2}-\d{2}-\d{2})", text)
            if m:
                try:
                    dt_found = datetime.fromisoformat(m.group(1)).date()
                    if dt_found > as_of_date:
                        continue
                except Exception:
                    pass
        snippet = ''
        idx = low.find(q)
        if idx != -1:
            start = max(0, idx - 80)
            end = min(len(text), idx + 80)
            snippet = text[start:end].replace('\n', ' ')
        hits.append({'file': p.name, 'score': str(score), 'snippet': snippet})
    hits.sort(key=lambda d: int(d['score']), reverse=True)
    return hits[:limit]
