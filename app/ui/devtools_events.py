"""
# ============================================================
# Context Banner — devtools_events | Category: ui
# Purpose: Lightweight Telemetrie-/Event-Hook für DevTools (lokal, kein Netzwerk) – Audit & Debug Unterstützung

# Contracts
#   emit(event: str, payload: dict) -> bool
#       - Fügt Event in In-Memory Ring-Puffer ein (max 100) wenn Flag aktiv (VEK_DEVTOOLS_VERBOSE=1)
#       - Rückgabe: True wenn gespeichert, False wenn verworfen (Flag off)
#   get_events(limit: int|None=None) -> list[dict]
#       - Liefert Kopie der letzten Events (FIFO innerhalb Ring). Optionales Limit (neueste zuerst)
#   clear_events() -> None
#       - Leert Puffer (Tests / manuelles Reset)

# Invariants
#   - Kein Netzwerk / kein File I/O
#   - Deterministisch (Reihenfolge = Insert Reihenfolge mod Ring-Kürzung)
#   - Keine externen Dependencies

# Dependencies
#   Internal: stdlib only
#   External: none

# Tests
#   tests/test_devtools_events.py

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from collections import deque
import os, time

_MAX_EVENTS = 100
_BUFFER: deque[Dict[str, Any]] = deque(maxlen=_MAX_EVENTS)


def _flag_enabled() -> bool:
    return bool(int(os.environ.get("VEK_DEVTOOLS_VERBOSE", "0")))


def emit(event: str, payload: Dict[str, Any]) -> bool:
    """Record an event if verbose flag active.

    Validation:
      - event: non-empty str
      - payload: dict (shallow copied)
    Returns False if flag disabled.
    Raises ValueError on invalid input types.
    """
    if not isinstance(event, str) or not event.strip():
        raise ValueError("event must be non-empty str")
    if not isinstance(payload, dict):
        raise ValueError("payload must be dict")
    if not _flag_enabled():
        return False
    rec = {
        "ts": time.time(),
        "event": event.strip(),
        "payload": dict(payload),  # shallow copy
    }
    _BUFFER.append(rec)
    return True


def get_events(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    items = list(_BUFFER)
    if limit is not None:
        return items[-limit:]
    return items


def clear_events() -> None:
    _BUFFER.clear()


__all__ = ["emit", "get_events", "clear_events"]
