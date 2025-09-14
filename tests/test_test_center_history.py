"""
Tests for extended Test Center history & run retrieval (Increment I1 optimal variant)
Focus:
 - list_test_center_runs returns recent runs (after executing a couple)
 - get_test_center_run returns specific run
 - negative unknown run id raises ValueError
"""
from app.ui import admin_devtools as adm_dt


def _run_once():
    # Use a very narrow filter to keep runtime low
    return adm_dt.run_test_center(k_expr="metrics")


def test_history_accumulates_and_lookup():
    r1 = _run_once()
    r2 = _run_once()
    hist = adm_dt.list_test_center_runs(limit=5)
    assert hist, "History should not be empty after runs"
    # Expect newest first in returned order
    assert hist[0]["run_id"] in {r1["run_id"], r2["run_id"]}
    # Lookup existing
    got = adm_dt.get_test_center_run(r1["run_id"])
    assert got["run_id"] == r1["run_id"]


def test_history_negative_lookup():
    import pytest
    with pytest.raises(ValueError):
        adm_dt.get_test_center_run("__no_such_run__")
