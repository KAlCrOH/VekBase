"""
# ============================================================
# Context Banner — test_testqueue_retry_output | Category: test
# Purpose: Verifiziert retry_run und Full Output Persistenz.
# ============================================================
"""
import os, pathlib, time
from app.core import testqueue as tq


def test_retry_and_full_output(monkeypatch):
    # Force tiny truncation to trigger full output file creation
    monkeypatch.setenv("VEK_TESTQUEUE_MAX_OUTPUT", "60")
    # Submit and process
    rid = tq.submit_run(k_expr="metrics")
    tq.process_next()
    st = tq.get_status(rid)
    assert st is not None
    # Retry
    new_id = tq.retry_run(rid)
    assert isinstance(new_id, str)
    tq.process_next()
    full = tq.get_full_output(rid)
    assert full is not None and "stdout" in full
    # If truncated, output files may exist
    base = pathlib.Path("data/devtools/testqueue_outputs")
    if st.get("stdout_truncated") or st.get("stderr_truncated"):
        assert any(p.name.startswith(rid) for p in base.glob(f"{rid}_*.out"))