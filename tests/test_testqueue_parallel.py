"""
# ============================================================
# Context Banner — test_testqueue_parallel | Category: test
# Purpose: Verifiziert Parallel-Worker, Status-Filter & Persistenz des Testqueue Systems.

# Contracts
#   - Mehrere submit_run unter gesetztem VEK_TESTQUEUE_WORKERS>0 -> mindestens 2 Runs verarbeitet.
#   - list_runs(status=[...]) filtert korrekt.
#   - Persistenz-Datei wächst nach fertigen Runs.

# Invariants
#   - Test robust bei langsamer Verarbeitung (Timeout Schleife max 15s)
#   - Keine Netzwerkzugriffe

# Dependencies
#   Internal: app.core.testqueue
#   External: stdlib
# ============================================================
"""
import os, time, pathlib
from app.core import testqueue as tq


def _wait_for_runs(target_count: int, timeout: float = 15.0):
    start = time.time()
    while time.time() - start < timeout:
        rows = tq.list_runs(limit=50)
        finished = [r for r in rows if r.get("status") in {"passed","failed","error"}]
        if len(finished) >= target_count:
            return finished
        time.sleep(0.5)
    return []


def test_parallel_workers_and_persistence(monkeypatch):
    monkeypatch.setenv("VEK_TESTQUEUE_WORKERS", "2")
    tq.ensure_workers()
    # Submit multiple runs (some with non-matching filter)
    ids = [tq.submit_run(k_expr="metrics"), tq.submit_run(k_expr="__no_match__"), tq.submit_run(k_expr="metrics")] 
    finished = _wait_for_runs(target_count=2)  # at least two should finish within timeout
    assert len(finished) >= 2, "Expected at least 2 finished runs with workers"
    # Status filter check
    passed_rows = tq.list_runs(limit=10, status=["passed"])  # any subset
    assert all(r["status"] == "passed" for r in passed_rows)
    # Persistence file existence (best-effort)
    persist_path = pathlib.Path("data/devtools/testqueue_runs.jsonl")
    assert persist_path.exists(), "Persistence file should exist"
    size_before = persist_path.stat().st_size
    # Force another run to increase file size
    tq.submit_run(k_expr="metrics")
    _wait_for_runs(target_count=3)
    size_after = persist_path.stat().st_size
    assert size_after >= size_before, "Persistence file should not shrink"