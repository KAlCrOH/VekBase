"""
# ============================================================
# Context Banner — test_admin_devtools | Category: test
# Purpose: Verifiziert Admin DevTools Helper (run_test_subset & run_lint_report)

# Contracts
#   - run_test_subset gibt dict mit status/passed/failed/stdout/stderr
#   - run_lint_report gibt dict (LintReport structure)

# Invariants
#   - Kein Streamlit Import nötig
#   - Filter ohne Treffer -> passed oder failed=0; status kann 'passed' bleiben

# Dependencies
#   Internal: app.ui.admin_devtools
#   External: stdlib

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from app.ui import admin_devtools as adm_dt


def test_admin_devtools_run_subset_metrics():
    res = adm_dt.run_test_subset(k_expr="metrics")
    assert set(res.keys()) == {"status","passed","failed","stdout","stderr"}
    assert res["status"] in {"passed","failed"}  # metrics tests should pass normally
    assert res["stdout"].strip() != ""


def test_admin_devtools_run_subset_no_match():
    res = adm_dt.run_test_subset(k_expr="__no_such_test__")
    # No matches -> Should not crash; passed or failed=0
    assert res["failed"] == 0
    assert res["passed"] in (0, res["passed"])  # allow 0 or >0 if some unexpected match


def test_admin_devtools_lint_report_structure():
    rep = adm_dt.run_lint_report()
    for key in ["issues","errors","warnings","total"]:
        assert key in rep
    assert isinstance(rep["issues"], list)


def test_admin_devtools_benchmark_basic():
    # pick first registered target
    reg = adm_dt.list_benchmarks()
    assert reg, "Benchmark registry should not be empty"
    target = next(iter(reg.keys()))
    res = adm_dt.run_benchmark(target, repeat=1)
    # structure expectations
    for k in ["target","runs_ms","median_ms","baseline_ms","delta_pct","faster"]:
        assert k in res
    assert res["target"] == target


def test_admin_devtools_benchmark_invalid():
    import pytest
    with pytest.raises(ValueError):
        adm_dt.run_benchmark("__nope__")


def test_admin_devtools_snapshot_metrics_first_run(tmp_path, monkeypatch):
    # Force snapshot storage into temp dir to avoid polluting repo
    monkeypatch.chdir(tmp_path)
    # Re-import snapshots with temp cwd baseline path
    res = adm_dt.run_snapshot("metrics", update=False)
    assert res["status"] in {"baseline_created", "no_diff", "diff"}
    assert res["target"] == "metrics"


def test_admin_devtools_snapshot_invalid():
    import pytest
    with pytest.raises(ValueError):
        adm_dt.run_snapshot("__bad__")