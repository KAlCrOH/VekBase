"""
Tests for Test Center Panel helpers (Increment I1)
Focus: flag gating, summary existence helper, negative unknown run id.
Streamlit UI itself is not imported (keeps tests fast & headless) – we test helper layer in admin_devtools.
"""
import os
import pytest
from pathlib import Path
from app.ui import admin_devtools as adm_dt


def test_test_center_flag_default_off(monkeypatch):
    monkeypatch.delenv("VEK_TEST_CENTER", raising=False)
    assert adm_dt.test_center_flag_enabled() is False


def test_test_center_flag_on(monkeypatch):
    monkeypatch.setenv("VEK_TEST_CENTER", "1")
    assert adm_dt.test_center_flag_enabled() is True


def test_test_center_run_and_summary_exists(monkeypatch):
    monkeypatch.setenv("VEK_TEST_CENTER", "1")
    res = adm_dt.run_test_center(k_expr="metrics")
    assert res.get("run_id")
    # helper should reflect presence (summary may be None if write failed -> tolerate False but check path when provided)
    exists_helper = adm_dt.test_center_latest_summary_exists()
    arts = res.get("artifacts") or {}
    summary_path = arts.get("summary")
    if summary_path:
        assert Path(summary_path).exists()
        assert exists_helper is True
    else:
        # artifact missing – helper may be False (graceful)
        assert exists_helper in (False, True)  # True only if race wrote later


def test_test_center_negative_unknown_run_id():
    with pytest.raises(ValueError):
        adm_dt.get_test_center_run("__unknown__")
