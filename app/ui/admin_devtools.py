"""
# ============================================================
# Context Banner — admin_devtools | Category: ui
# Purpose: Streamlit-unabhängige Helper für Admin/Console DevTools (Tests, Lint, Benchmarks, Snapshots, Queued Test Runner)

# Contracts
#   run_test_subset(k_expr) -> dict(status, passed, failed, stdout, stderr)
#   run_lint_report() -> dict (LintReport)
#   run_benchmark(target, repeat) -> dict (inkl. Persist Delta)
#   run_snapshot(target, update) -> dict (Diff & Summary)
#   Queue API: submit_test_run, list_test_runs(status?, include_persisted), get_test_run, get_test_run_output, retry_test_run
#   Alle Funktionen Streamlit-frei → unit-testbar
#
# Invariants
#   - Keine neuen externen Dependencies
#   - Queue Persistenz: data/devtools/testqueue_runs.jsonl + testqueue_outputs/*.out (über core.testqueue)
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
from app.core import testqueue as _tq  # queued test runner (parallel/persistent)


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
    return ["metrics", "equity_curve", "equity_curve_unrealized", "equity_curve_per_ticker"]


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
    # queue api
    "submit_test_run","get_test_run","list_test_runs","process_test_queue","ensure_testqueue_workers","get_test_run_output","retry_test_run","get_queue_aggregates",
]


# --- Increment: Queued Test Runner (prompt3_roadmap_implement) ---
def submit_test_run(k_expr: str | None = None, module_substr: str | None = None) -> str:
    return _tq.submit_run(k_expr=k_expr, module_substr=module_substr)


def get_test_run(run_id: str):
    return _tq.get_status(run_id)


def list_test_runs(limit: int = 20, status: list[str] | None = None, include_persisted: bool = True):
    # Legacy tick (still supports non-worker mode); in worker mode active runs progress asynchronously
    _tq.process_next()
    return _tq.list_runs(limit=limit, status=status, include_persisted=include_persisted)


def process_test_queue():  # optional explicit tick
    return _tq.process_next()


def ensure_testqueue_workers():
    return _tq.ensure_workers()


def get_test_run_output(run_id: str):
    return _tq.get_full_output(run_id)


def retry_test_run(run_id: str):
    return _tq.retry_run(run_id)


def get_queue_aggregates(limit: int = 100):
    """Return simple aggregate metrics for recent finished runs (core.testqueue.aggregate_metrics)."""
    return _tq.aggregate_metrics(limit=limit)
