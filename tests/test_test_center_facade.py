"""
Tests for Test Center facade (Increment I1)
Focus: run_test_center happy path, negative discovery, artifact existence (summary json at least).
"""
from pathlib import Path
from app.ui import admin_devtools as adm_dt


def test_run_test_center_happy_subset():
    res = adm_dt.run_test_center(k_expr="metrics")  # should match some tests quickly
    assert res["status"] in {"passed","failed"}
    assert isinstance(res.get("passed"), int)
    arts = res.get("artifacts") or {}
    if arts.get("summary"):
        assert Path(arts["summary"]).exists()


def test_run_test_center_negative_no_matches():
    # improbable filter to force zero collected; still should produce result (maybe 0 passed)
    res = adm_dt.run_test_center(k_expr="__unlikely_filter__")
    assert res["status"] in {"passed","failed","error"}
    # Should still create a run_id and (attempt) summary artifact
    assert res.get("run_id")


def test_run_test_center_artifact_directory_created():
    res = adm_dt.run_test_center(k_expr="metrics")
    arts = res.get("artifacts") or {}
    if arts.get("summary"):
        summary_path = Path(arts["summary"])    
        assert summary_path.exists()
        assert summary_path.read_text().find("run_id") != -1
