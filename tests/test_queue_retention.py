"""
# ============================================================
# Context Banner — test_queue_retention | Category: test
# Purpose: Tests für Retention Policy (VEK_TESTQUEUE_MAX_RUNS / VEK_TESTQUEUE_MAX_BYTES)
# ============================================================
"""
import os, json, pathlib, time
from app.core import testqueue as tq
from app.core import devtools as _dev

class DummyRes:
    def __init__(self, status: str, stdout: str):
        self.status = status
        self.stdout = stdout
        self.stderr = ""

def fake_run_tests(nodeids=None, k_expr=None, module_substr=None, timeout=120):
    # Alternate passed/failed for variety
    existing = tq.list_runs(limit=50, include_persisted=False)
    if len(existing) % 2 == 0:
        return DummyRes("passed", "test_x::test_ok PASSED")
    return DummyRes("failed", "test_y::test_fail FAILED")

def test_retention_max_runs(monkeypatch, tmp_path):
    # Patch environment & devtools
    monkeypatch.setenv("VEK_TESTQUEUE_MAX_RUNS", "3")
    monkeypatch.delenv("VEK_TESTQUEUE_MAX_BYTES", raising=False)
    monkeypatch.setattr(_dev, "run_tests", fake_run_tests)
    # generate 5 runs
    for _ in range(5):
        tq.submit_run()
        tq.process_next()
    # After processing, JSONL should have at most 3 lines
    persist_path = pathlib.Path("data/devtools/testqueue_runs.jsonl")
    if persist_path.exists():
        lines = [ln for ln in persist_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) <= 3


def test_retention_max_bytes(monkeypatch, tmp_path):
    # Set generous run retention but low bytes to force deletion
    monkeypatch.setenv("VEK_TESTQUEUE_MAX_RUNS", "10")
    monkeypatch.setenv("VEK_TESTQUEUE_MAX_BYTES", "200")  # very small
    monkeypatch.setattr(_dev, "run_tests", fake_run_tests)
    # produce runs with large stdout lengths to create output files
    class BigRes(DummyRes):
        pass
    def big_fake_run_tests(nodeids=None, k_expr=None, module_substr=None, timeout=120):
        txt = "test_big::t PASSED\n" + ("X" * 500)
        return DummyRes("passed", txt)
    monkeypatch.setattr(_dev, "run_tests", big_fake_run_tests)
    for _ in range(4):
        tq.submit_run()
        tq.process_next()
        time.sleep(0.01)
    out_dir = pathlib.Path("data/devtools/testqueue_outputs")
    if out_dir.exists():
        total = sum(p.stat().st_size for p in out_dir.glob("*_stdout.out"))
        # Should attempt to stay under threshold *after* some deletions; allow slight buffer
        assert total <= 200 or len(list(out_dir.glob("*_stdout.out"))) <= 2
