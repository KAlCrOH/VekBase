"""
# ============================================================
# Context Banner — devtools_output_filter | Category: ui
# Purpose: Filter-/Selektions-Helper für DevTools Test Output Sektionen (stdout, stderr, summary)

# Contracts
#   filter_output_sections(data: dict, sections: list[str]) -> dict
#       - data kann Keys 'stdout','stderr','summary' enthalten (summary=dict)
#       - sections Liste gewünschter Sektionen; unbekannte Sektionen werden ignoriert
#       - Validierung: sections muss Liste von str; ValueError sonst
#       - Rückgabe: neues Dict nur mit vorhandenen & erlaubten Keys in gewünschter Reihenfolge (Insertion Order)

# Invariants
#   - Rein funktional; keine Seiteneffekte
#   - Keine externen Dependencies
#   - Deterministisch

# Dependencies
#   Internal: none
#   External: stdlib only

# Tests
#   tests/test_devtools_output_filter.py

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from __future__ import annotations
from typing import Dict, Any, List

ALLOWED = ["stdout", "stderr", "summary"]


def filter_output_sections(data: Dict[str, Any] | None, sections: List[str] | None) -> Dict[str, Any]:
    if data is None:
        data = {}
    # Strict: None ist ungültig (Tests erwarten ValueError)
    if sections is None:
        raise ValueError("sections must be list[str] (got None)")
    if not isinstance(sections, list) or not all(isinstance(s, str) for s in sections):
        raise ValueError("sections must be list[str]")
    out: Dict[str, Any] = {}
    for s in sections:
        if s in ALLOWED and s in data:
            out[s] = data[s]
    return out


__all__ = ["filter_output_sections"]
