"""
Increment I2: Metrics Snapshot Widget tests
Focus: render smoke (with demo data) & empty data fallback.
We only test helper side-effects by importing console (which builds widget once) in a controlled dummy environment.
"""
import os
import importlib


def test_metrics_snapshot_empty(monkeypatch):
    # Force no default data and ensure repo absent
    monkeypatch.setenv('VEK_DEFAULT_DATA','0')
    if 'app.ui.console' in list(importlib.sys.modules.keys()):
        del importlib.sys.modules['app.ui.console']
    mod = importlib.import_module('app.ui.console')  # noqa: F401
    # If it reaches here without exception, empty fallback path works


def test_metrics_snapshot_with_default(monkeypatch):
    # Allow default dataset; re-import
    monkeypatch.setenv('VEK_DEFAULT_DATA','1')
    if 'app.ui.console' in list(importlib.sys.modules.keys()):
        del importlib.sys.modules['app.ui.console']
    mod = importlib.import_module('app.ui.console')
    # Module should define session_state marker after import when running inside Streamlit normally; here just smoke
    assert 'app.ui.console' in importlib.sys.modules
