"""
# ============================================================
# Context Banner — test_queue_metrics_ext | Category: test
# Purpose: Tests für erweiterte queue aggregate metrics (median, p95)
# ============================================================
"""
import time
from app.core import testqueue as tq


def test_queue_aggregate_metrics_extended(monkeypatch):
    # ensure isolated state (previous runs may inflate counts)
    if hasattr(tq, '_reset_state_for_tests'):
        tq._reset_state_for_tests()  # type: ignore
    # submit few synthetic runs by monkeypatching execution to control duration
    orig_execute = tq._execute  # type: ignore
    durations = [0.01, 0.02, 0.05, 0.10, 0.20]
    calls = {"i": 0}
    def fake_execute(run):  # type: ignore
        run.started_at = time.time()
        time.sleep(durations[calls["i"]])
        run.status = "passed"
        run.passed = 1
        run.failed = 0
        run.stdout = "ok"
        run.stderr = ""
        run.finished_at = time.time()
        run.duration_s = run.finished_at - run.started_at
        calls["i"] += 1
    monkeypatch.setattr(tq, '_execute', fake_execute)
    # queue runs
    ids = [tq.submit_run(k_expr=None) for _ in durations]
    for _id in ids:
        tq.process_next()
    agg = tq.aggregate_metrics(limit=10)
    assert agg['total_runs'] == len(durations)
    assert agg['median_duration_s'] is not None
    assert agg['p95_duration_s'] is not None
    # p95 should be near the max (maybe last value depending on rounding)
    assert agg['p95_duration_s'] <= max(durations) + 0.05
    monkeypatch.setattr(tq, '_execute', orig_execute)
