"""
# ============================================================
# Context Banner — devtools_panel_helpers | Category: ui
# Purpose: Kleine, wiederverwendbare Hilfsfunktionen für DevTools Panels (Queue Runs Formatierung)

# Contracts
#   format_queue_rows(rows: list[dict]) -> list[dict]
#       - Normalisiert Queue-Run Datensätze für tabellarische Anzeige (füllt fehlende Schlüssel)
#       - Erwartet Liste von Dicts; ValueError bei ungültigem Inputtyp
#       - Fügt fehlende Pflichtfelder mit Default-Werten hinzu
#   REQUIRED_KEYS (intern): Minimaler Schlüssel-Satz für UI Konsistenz
#
# Invariants
#   - Keine externen Dependencies
#   - Rein funktional / deterministisch
#   - Kein I/O, keine Seiteneffekte
#
# Dependencies
#   Internal: none
#   External: stdlib only
#
# Tests
#   tests/test_devtools_panel_helpers.py (Positiv + Negativfall)
#
# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from __future__ import annotations
from typing import List, Dict, Any

REQUIRED_KEYS = [
    "run_id",
    "status",
    "passed",
    "failed",
]


def format_queue_rows(rows: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
    """Return a normalized copy of queue run rows.

    Behavior:
      - Validates input type (list of dict). Raises ValueError otherwise.
      - Ensures REQUIRED_KEYS exist (with defaults if missing):
          run_id: str -> fallback ''
          status: str -> fallback 'unknown'
          passed/failed: int -> fallback 0 (coerces non-int numeric)
      - Leaves other keys unverändert.
      - Returns new list (defensiv), Original wird nicht mutiert.
    """
    if rows is None:
        raise ValueError("rows must be a list, got None")
    if not isinstance(rows, list):
        raise ValueError(f"rows must be a list, got {type(rows)!r}")
    norm: List[Dict[str, Any]] = []
    for idx, r in enumerate(rows):
        if not isinstance(r, dict):
            raise ValueError(f"row index {idx} is not a dict: {type(r)!r}")
        c = dict(r)  # shallow copy
        # run_id
        if "run_id" not in c:
            c["run_id"] = ""
        # status
        if not c.get("status"):
            c["status"] = "unknown"
        # passed / failed numeric coercion
        for k in ("passed", "failed"):
            if k not in c:
                c[k] = 0
            else:
                v = c[k]
                if isinstance(v, bool):  # avoid bool as int confusion
                    c[k] = int(v)
                elif isinstance(v, (int, float)):
                    c[k] = int(v)
                else:
                    # Non-numeric -> default 0
                    c[k] = 0
        norm.append(c)
    return norm


__all__ = ["format_queue_rows"]
