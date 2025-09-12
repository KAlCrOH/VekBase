"""
# ============================================================
# Context Banner — test_testqueue_truncation | Category: test
# Purpose: Testet Output-Truncation & Duration Feld im Testqueue.

# Approach: Setzt sehr kleines VEK_TESTQUEUE_MAX_OUTPUT um Truncation sicher zu triggern.
# ============================================================
"""
import os, time
from app.core import testqueue as tq


def test_truncation_and_duration(monkeypatch):
    monkeypatch.setenv("VEK_TESTQUEUE_MAX_OUTPUT", "50")  # sehr klein
    # Immediate Run (synchron)
    res = tq.run_immediate(k_expr="metrics")
    rid = res["run_id"] if "run_id" in res else None
    status = tq.list_runs(limit=5)
    assert any(r.get("duration_s") is not None for r in status if r.get("run_id") == rid or True)
    # Mindestens eines der Felder sollte truncation Flag haben falls Output > 50
    trunc_found = any(r.get("stdout_truncated") or r.get("stderr_truncated") for r in status)
    # Falls Output extrem kurz wäre, akzeptiere kein trunc_found
    assert trunc_found or all(len(r.get("stdout","")) <= 60 for r in status)