"""
# ============================================================
# Context Banner — test_queue_aggregates | Category: test
# Purpose: Tests für Aggregationsfunktion core.testqueue.aggregate_metrics
# Contracts
#   - aggregate_metrics() -> dict mit pass/fail/error rates & mean duration
#   - Edge Cases: keine finished runs
# Invariants
#   - Keine Netzwerkzugriffe
#   - Nutzt nur In-Memory Queue State
# ============================================================
"""
from app.core import testqueue as tq
from app.core import devtools as _dev


def test_aggregate_metrics_empty():
    # Leerer Zustand -> alle Raten 0, mean_duration None
    ag = tq.aggregate_metrics()
    assert ag["total_runs"] == 0
    assert ag["pass_rate"] == 0.0 and ag["fail_rate"] == 0.0 and ag["error_rate"] == 0.0
    assert ag["mean_duration_s"] is None


def test_aggregate_metrics_after_runs(monkeypatch):
    # Simuliere zwei Runs (1 passed, 1 failed) durch direkte submit+process
    # Monkeypatch devtools.run_tests to produce deterministic outcomes quickly
    class DummyRes:
        def __init__(self, status, stdout):
            self.status = status
            self.stdout = stdout
            self.stderr = ""
    def fake_run_tests(nodeids=None, k_expr=None, module_substr=None, timeout=120):
        # Alternate status based on count of existing history
        # Access internal _HISTORY length via public list_runs finished filter
        existing = tq.list_runs(limit=5, include_persisted=False)
        if len(existing) % 2 == 0:
            return DummyRes("passed", "test_x::test_ok PASSED")
        return DummyRes("failed", "test_y::test_fail FAILED")
    monkeypatch.setattr(_dev, "run_tests", fake_run_tests)
    # Submit two runs and process synchron synchronously
    rid1 = tq.submit_run(k_expr=None)
    tq.process_next()
    rid2 = tq.submit_run(k_expr=None)
    tq.process_next()
    ag = tq.aggregate_metrics()
    assert ag["total_runs"] >= 2
    # pass_rate + fail_rate should sum to ~1 (no errors)
    assert abs((ag["pass_rate"] + ag["fail_rate"]) - 1.0) < 0.01
    assert ag["error_rate"] == 0.0
