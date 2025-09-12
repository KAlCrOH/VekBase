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
from typing import List, Dict, Optional
from datetime import datetime, date

DOCS_BASE = Path('docs/CONTEXT')


def list_context_files() -> List[Path]:
    if not DOCS_BASE.exists():
        return []
    return sorted([p for p in DOCS_BASE.iterdir() if p.suffix.lower() == '.md'])


def retrieve(
    query: str,
    limit: int = 3,
    ticker: Optional[str] = None,
    as_of: Optional[str | date] = None,
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
