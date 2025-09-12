"""
# ============================================================
# Context Banner — test_devtools_shared | Category: test
# Purpose: Tests für devtools_shared Wrapper (Smoke + Negativfall)

# Contracts
#   - discover_tests returns list
#   - run_tests returns dict with status / counts
#   - run_lint returns dict with issues
#   - run_benchmark returns dict with expected keys
#   - snapshot returns dict with status

# Invariants
#   - Deterministic for stable codebase

# Dependencies
#   Internal: app.ui.devtools_shared
#   External: stdlib

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from app.ui import devtools_shared as dsh
import pytest


def test_devtools_shared_discover_and_run():
    nodeids = dsh.discover_tests(k_expr="metrics", module_substr="test_metrics")
    assert any("test_metrics.py::" in n for n in nodeids)
    res = dsh.run_tests(nodeids=nodeids[:1])
    assert res["status"] in {"passed","failed"}
    assert "stdout" in res and res["stdout"].strip() != ""


def test_devtools_shared_lint_and_benchmark_and_snapshot():
    lint_rep = dsh.run_lint()
    assert set(["issues","errors","warnings","total"]).issubset(lint_rep.keys())
    breg = dsh.list_benchmarks()
    assert breg
    target = next(iter(breg.keys()))
    bench_res = dsh.run_benchmark(target, repeat=1)
    for k in ["target","runs_ms","median_ms"]:
        assert k in bench_res
    snap_res = dsh.snapshot("metrics", update=False)
    assert snap_res["status"] in {"baseline_created","no_diff","diff","updated"}
    # Extended keys
    assert "summary" in snap_res
    summary = snap_res["summary"]
    assert set(["status","target","diff_count","updated","has_diff"]).issubset(summary.keys())
    assert summary["status"] == snap_res["status"]
    assert summary["target"] == "metrics"
    assert "numeric_deltas" in snap_res
    # numeric_deltas may be empty depending on baseline state; if non-empty, required keys
    for row in snap_res["numeric_deltas"]:
        assert set(["path","baseline","current","delta","delta_pct"]).issubset(row.keys())


def test_devtools_shared_run_invalid_nodeid():
    res = dsh.run_tests(nodeids=["tests/test_nonexistent_module.py::test_nowhere"])
    assert res["status"] == "failed"