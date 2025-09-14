"""
# ============================================================
# Context Banner — test_testqueue_persistence_errors | Category: test
# Purpose: Tests für Persistence Error Tracking im testqueue Modul
# ============================================================
"""
import os, pathlib
from app.core import testqueue as tq


def test_persistence_error_counters(monkeypatch, tmp_path):
    # Force persistence path into unwritable directory by mocking open
    class Boom(IOError):
        pass
    import builtins
    def boom_open(*args, **kwargs):  # type: ignore
        raise Boom("forced persistence failure")
    monkeypatch.setattr(builtins, 'open', boom_open)
    rid = tq.submit_run(k_expr='metrics')
    # process synchron synchronously
    tq.process_next()
    stats = tq.get_persistence_stats()
    assert stats['errors_total'] >= 1
    assert 'forced persistence failure' in (stats['last_error'] or '')
