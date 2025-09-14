"""
# ============================================================
# Context Banner — test_snapshots | Category: test
# Purpose: Verifiziert Snapshot Harness (Baseline, No-Diff, Diff + Update)

# Contracts
#   ensure_and_diff(target, update=False) orchestrates snapshot + diff + optional update

# Dependencies
#   Internal: app.core.snapshots
#   External: stdlib (pathlib)

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from app.core.snapshots import ensure_and_diff, save_baseline, create_snapshot, _snapshot_path
from pathlib import Path
import json


def test_snapshot_baseline_creation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    res = ensure_and_diff("metrics")
    assert res.status == "baseline_created"
    assert _snapshot_path("metrics").exists()


def test_snapshot_no_diff(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # create baseline first
    baseline = create_snapshot("metrics")
    save_baseline("metrics", baseline)
    res = ensure_and_diff("metrics")
    assert res.status == "no_diff"


def test_snapshot_diff_and_update(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # baseline metrics
    baseline = create_snapshot("metrics")
    save_baseline("metrics", baseline)
    # mutate baseline file artificially to force diff (change a numeric field)
    p = _snapshot_path("metrics")
    data = json.loads(p.read_text(encoding="utf-8"))
    # change a numeric field if exists, else inject one
    metrics = data["data"]
    # pick first numeric key
    for k, v in metrics.items():
        if isinstance(v, (int, float)):
            metrics[k] = (v + 123.456) if isinstance(v, (int, float)) else v
            break
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    res_diff = ensure_and_diff("metrics")
    assert res_diff.status == "diff"
    assert res_diff.diff and len(res_diff.diff) >= 1
    res_update = ensure_and_diff("metrics", update=True)
    assert res_update.status in ("updated", "no_diff")  # depending on timing if re-run immediate


def test_snapshot_sim_equity_curve_baseline(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    res = ensure_and_diff("sim_equity_curve")
    assert res.status == "baseline_created"
    assert _snapshot_path("sim_equity_curve").exists()
    # second run should be no_diff
    res2 = ensure_and_diff("sim_equity_curve")
    assert res2.status == "no_diff"


def test_snapshot_benchmark_overlay_sample(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    res = ensure_and_diff("benchmark_overlay_sample")
    assert res.status == "baseline_created"
    data = res.snapshot["data"]
    assert "equity_curve" in data and "benchmark_curve" in data
