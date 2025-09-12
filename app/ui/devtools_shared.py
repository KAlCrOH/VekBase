"""
# ============================================================
# Context Banner — devtools_shared | Category: ui
# Purpose: Gemeinsame Wrapper für DevTools Funktionen (Tests, Lint, Benchmark, Snapshot) zur Wiederverwendung in Console & Admin UIs.

# Contracts
#   discover_tests(k_expr:str|None, module_substr:str|None) -> list[str]
#   run_tests(nodeids:list[str]|None, k_expr:str|None, module_substr:str|None) -> dict(status,stdout,stderr,passed,failed)
#   run_lint() -> dict (LintReport)
#   list_benchmarks() -> dict[target->desc]
#   run_benchmark(target, repeat:int) -> dict
#   snapshot(target, update:bool=False) -> dict

# Invariants
#   - Delegation only; no UI framework dependency
#   - Deterministic for same codebase state

# Dependencies
#   Internal: app.core.devtools, linttools, benchtools, snapshots
#   External: stdlib

# Tests
#   tests/test_devtools_shared.py

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from app.core import devtools as _dev
from app.core import linttools as _lint
from app.core import benchtools as _bench
from app.core import snapshots as _snap


def discover_tests(k_expr: Optional[str] = None, module_substr: Optional[str] = None) -> List[str]:
    return _dev.discover_tests(k_expr=k_expr, module_substr=module_substr)


def run_tests(nodeids: Optional[List[str]] = None, k_expr: Optional[str] = None, module_substr: Optional[str] = None) -> Dict[str, Any]:
    res = _dev.run_tests(nodeids=nodeids, k_expr=k_expr, module_substr=module_substr)
    summary = _dev.parse_summary(res.stdout)
    return {
        "status": res.status,
        "stdout": res.stdout,
        "stderr": res.stderr,
        "passed": summary["passed"],
        "failed": summary["failed"],
    }


def run_lint() -> Dict[str, Any]:
    return _lint.run_lint().to_dict()


def list_benchmarks() -> Dict[str, str]:
    return _bench.get_registry()


def run_benchmark(target: str, repeat: int = 3) -> Dict[str, Any]:
    return _bench.run_benchmark(target, repeat=repeat).to_dict()


def _extract_numeric_deltas(diff_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for d in diff_list:
        base = d.get("baseline")
        cur = d.get("current")
        # Only numeric scalars qualify
        if isinstance(base, (int, float)) and isinstance(cur, (int, float)):
            try:
                delta = cur - base
                pct = (delta / base * 100.0) if base not in (0, None) else None
            except Exception:
                delta, pct = None, None
            rows.append({
                "path": d.get("path"),
                "baseline": base,
                "current": cur,
                "delta": delta,
                "delta_pct": pct,
            })
    return rows


def snapshot(target: str, update: bool = False) -> Dict[str, Any]:
    """Extended snapshot wrapper adding summary + numeric delta rows.

    Returns original keys plus:
      summary: {status,target,diff_count,updated,has_diff}
      numeric_deltas: list[{path,baseline,current,delta,delta_pct}]
    Non-breaking: existing callers can ignore new keys.
    """
    res = _snap.ensure_and_diff(target, update=update).to_dict()
    diff_list = res.get("diff") or []
    summary = {
        "status": res.get("status"),
        "target": res.get("target"),
        "diff_count": len(diff_list),
        "updated": res.get("status") == "updated",
        "has_diff": res.get("status") in {"diff", "updated"},
    }
    res["summary"] = summary
    if diff_list:
        res["numeric_deltas"] = _extract_numeric_deltas(diff_list)
    else:
        res["numeric_deltas"] = []
    return res


__all__ = [
    "discover_tests",
    "run_tests",
    "run_lint",
    "list_benchmarks",
    "run_benchmark",
    "snapshot",
]
