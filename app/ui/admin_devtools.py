"""
# ============================================================
# Context Banner — admin_devtools | Category: ui
# Purpose: Streamlit-unabhängige Helper für Admin-DevTools (Test/Lint) – thin wrapper über core.devtools & core.linttools

# Contracts
#   run_test_subset(k_expr: str|None) -> dict(status, passed, failed, stdout, stderr)
#     - Führt Tests via core.devtools.run_tests (Filter -k) aus
#   run_lint_report() -> dict (LintReport.to_dict())
#   Beide Funktionen: Keine Streamlit Abhängigkeit -> unit-testbar
#
# Invariants
#   - Keine neuen externen Dependencies
#   - Keine sys.path Hacks
#   - Deterministisch für stabile Codebasis
#
# Dependencies
#   Internal: app.core.devtools, app.core.linttools
#   External: stdlib
#
# Tests
#   tests/test_admin_devtools.py
#
# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from app.core import devtools as _dev
from app.core import linttools as _lint
from app.core import benchtools as _bench
from app.core import snapshots as _snap


def run_test_subset(k_expr: Optional[str] = None, max_tests: int = 10) -> Dict[str, Any]:
    """Run (optionally filtered) tests with a soft cap to keep runtime low in Admin UI.
    Strategy:
      1. If k_expr provided -> discover nodeids via devtools.discover_tests(k_expr)
      2. Limit to first `max_tests` nodeids (deterministic order from pytest)
      3. Run those nodeids directly (faster than full -k run)
      4. If discovery yields no tests, fallback to k_expr run (may return passed=0)
    Returns dict(status, passed, failed, stdout, stderr).
    Any discovery exception is converted into status 'error' with stderr message.
    """
    nodeids: Optional[list[str]] = None
    if k_expr:
        try:
            discovered = _dev.discover_tests(k_expr=k_expr, module_substr=None)
            if discovered:
                nodeids = discovered[:max_tests]
        except Exception as e:  # discovery failed
            return {"status": "error", "passed": 0, "failed": 0, "stdout": "", "stderr": f"discovery error: {e}"}
    # Run tests (either subset nodeids or fallback full expression)
    res = _dev.run_tests(nodeids=nodeids, k_expr=None if nodeids else (k_expr or None), module_substr=None, timeout=300)
    summary = _dev.parse_summary(res.stdout)
    return {
        "status": res.status,
        "passed": summary["passed"],
        "failed": summary["failed"],
        "stdout": res.stdout,
        "stderr": res.stderr,
    }


def run_lint_report() -> Dict[str, Any]:
    rep = _lint.run_lint().to_dict()
    return rep


def run_benchmark(target: str, repeat: int = 3) -> Dict[str, Any]:
    """Execute a registered benchmark target and return its dict representation.
    Negative case: unknown target -> ValueError propagated to caller (UI handles).
    """
    res = _bench.run_benchmark(target=target, repeat=repeat, persist=True)
    return res.to_dict()


def list_benchmarks() -> Dict[str, str]:
    return _bench.get_registry()


# Snapshot wrappers
def list_snapshot_targets() -> list[str]:
    return ["metrics", "equity_curve"]


def run_snapshot(target: str, update: bool = False) -> Dict[str, Any]:
    if target not in list_snapshot_targets():
        raise ValueError(f"Unknown snapshot target: {target}")
    res = _snap.ensure_and_diff(target, update=update)
    return res.to_dict()


__all__ = [
    "run_test_subset",
    "run_lint_report",
    "run_benchmark",
    "list_benchmarks",
    "list_snapshot_targets",
    "run_snapshot",
]
