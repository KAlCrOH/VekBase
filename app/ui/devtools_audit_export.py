"""
# ============================================================
# Context Banner — devtools_audit_export | Category: ui
# Purpose: Export-Hilfen für letzten Testlauf (Audit / Offline Review) – JSON & CSV In-Memory Strings

# Contracts
#   build_last_run_payload(state: dict) -> dict | None
#       - Erwartet Keys: status(str), summary(dict with passed/failed), stdout(str), stderr(str|"" optional)
#       - Rückgabe None falls Pflichtdaten fehlen (z.B. noch kein Lauf)
#   export_json(state: dict) -> str | None
#       - Serialisiert build_last_run_payload zu JSON (ensure_ascii=False, indent=2)
#   export_csv(state: dict) -> str | None
#       - Flache CSV-Zeile: status,passed,failed,stdout_lines,stderr_lines

# Invariants
#   - Kein File I/O, Netzwerk, Seiteneffekte
#   - Rein deterministisch

# Tests
#   tests/test_devtools_audit_export.py

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from __future__ import annotations
from typing import Dict, Any, Optional
import json, csv, io

def build_last_run_payload(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(state, dict):
        raise ValueError("state must be dict")
    if not state.get("status") or not isinstance(state.get("summary"), dict):
        return None
    summ = state["summary"]
    if "passed" not in summ or "failed" not in summ:
        return None
    payload = {
        "status": state.get("status"),
        "passed": int(summ.get("passed", 0)),
        "failed": int(summ.get("failed", 0)),
        "stdout": state.get("stdout") or "",
        "stderr": state.get("stderr") or "",
    }
    return payload


def export_json(state: Dict[str, Any]) -> Optional[str]:
    payload = build_last_run_payload(state)
    if not payload:
        return None
    return json.dumps(payload, ensure_ascii=False, indent=2)


def export_csv(state: Dict[str, Any]) -> Optional[str]:
    payload = build_last_run_payload(state)
    if not payload:
        return None
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["status","passed","failed","stdout_lines","stderr_lines"])
    writer.writeheader()
    writer.writerow({
        "status": payload["status"],
        "passed": payload["passed"],
        "failed": payload["failed"],
        "stdout_lines": len(payload["stdout"].splitlines()) if payload["stdout"] else 0,
        "stderr_lines": len(payload["stderr"].splitlines()) if payload["stderr"] else 0,
    })
    return buf.getvalue()


__all__ = ["build_last_run_payload", "export_json", "export_csv"]
