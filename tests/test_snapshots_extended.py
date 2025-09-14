"""
# ============================================================
# Context Banner — test_snapshots_extended | Category: test
# Purpose: Tests für neue Snapshot Targets (unrealized + per-ticker)
# ============================================================
"""
from app.core.snapshots import ensure_and_diff, create_snapshot, save_baseline, _snapshot_path
from pathlib import Path
import json

NEW_TARGETS = ["equity_curve_unrealized", "equity_curve_per_ticker"]

def test_new_snapshot_targets_baseline(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for tgt in NEW_TARGETS:
        res = ensure_and_diff(tgt)
        assert res.status == "baseline_created"
        assert _snapshot_path(tgt).exists()

def test_new_snapshot_targets_no_diff(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for tgt in NEW_TARGETS:
        snap = create_snapshot(tgt)
        save_baseline(tgt, snap)
        res = ensure_and_diff(tgt)
        assert res.status == "no_diff"
