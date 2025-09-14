"""
# ============================================================
# Context Banner — devtools_session_log | Category: ui
# Purpose: Per-Session Speicher für Test Run Kurz-Datensätze (rein In-Memory) – erleichtert Verlauf & Audit im UI

# Contracts
#   add_test_run(entry: dict) -> None
#       Required Keys: status(str), passed(int), failed(int)
#       Optional: selected(int), ts(float epoch seconds) (auto gesetzt falls fehlt)
#       Validation: Typen & Werte (non-negative ints)
#   list_test_runs(limit:int|None=None, status:list[str]|None=None) -> list[dict]
#       - Gibt Kopien in Einfügereihenfolge (älteste zuerst) zurück; optional gefiltert.
#   clear_test_runs() -> None
#   MAX_SESSION_RUNS (intern): 50

# Invariants
#   - Kein File I/O / Netzwerk
#   - Ring-Puffer (FIFO Kürzung) – deterministisch
#   - Keine externen Dependencies

# Tests
#   tests/test_devtools_session_log.py

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from collections import deque
import time

MAX_SESSION_RUNS = 50
_RUNS: deque[Dict[str, Any]] = deque(maxlen=MAX_SESSION_RUNS)


def add_test_run(entry: Dict[str, Any]) -> None:
    if not isinstance(entry, dict):
        raise ValueError("entry must be dict")
    required = ["status", "passed", "failed"]
    for k in required:
        if k not in entry:
            raise ValueError(f"missing key: {k}")
    status = entry["status"]
    if not isinstance(status, str) or not status:
        raise ValueError("status must be non-empty str")
    for k in ["passed", "failed"]:
        v = entry[k]
        if not isinstance(v, (int, float)) or v < 0:
            raise ValueError(f"{k} must be >=0 numeric")
        entry[k] = int(v)
    # optional selected
    if "selected" in entry:
        sel = entry["selected"]
        if not isinstance(sel, (int, float)) or sel < 0:
            raise ValueError("selected must be >=0 numeric if present")
        entry["selected"] = int(sel)
    if "ts" not in entry:
        entry["ts"] = time.time()
    # Shallow copy to avoid external mutation
    _RUNS.append(dict(entry))


def list_test_runs(limit: Optional[int] = None, status: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    items = list(_RUNS)
    if status:
        status_set = set(status)
        items = [r for r in items if r.get("status") in status_set]
    if limit is not None:
        items = items[-limit:]
    return [dict(r) for r in items]


def clear_test_runs() -> None:
    _RUNS.clear()


__all__ = ["add_test_run", "list_test_runs", "clear_test_runs", "MAX_SESSION_RUNS"]
