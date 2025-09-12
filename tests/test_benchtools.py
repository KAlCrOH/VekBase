"""
# ============================================================
# Context Banner — test_benchtools | Category: test
# Purpose: Verifiziert Benchmark Harness (Median & Baseline Persistenz)

# Contracts
#   Inputs: target name, repeat
#   Outputs: BenchmarkResult Felder
#   Determinism: Zeiten variieren leicht, Assertions nutzen Toleranzen/Existenzchecks

# Dependencies
#   Internal: app.core.benchtools
#   External: stdlib (pathlib, json)

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from app.core.benchtools import run_benchmark, get_registry
from pathlib import Path
import json


def test_registry_contains_targets():
    reg = get_registry()
    assert "aggregate_metrics" in reg
    assert "realized_equity_curve" in reg


def test_run_benchmark_and_persist(tmp_path, monkeypatch):
    # Redirect data/devtools to temp dir
    dev_dir = tmp_path / "data" / "devtools"
    monkeypatch.chdir(tmp_path)
    dev_dir.mkdir(parents=True, exist_ok=True)
    # First run (no baseline)
    res1 = run_benchmark("aggregate_metrics", repeat=2, persist=True)
    assert res1.target == "aggregate_metrics"
    assert len(res1.runs_ms) == 2
    assert res1.baseline_ms is None
    # Second run (baseline exists)
    res2 = run_benchmark("aggregate_metrics", repeat=2, persist=True)
    assert res2.baseline_ms is not None
    # median must be >0
    assert res2.median_ms > 0
    # Baseline file exists
    baseline_file = Path("data/devtools/bench_aggregate_metrics.json")
    assert baseline_file.exists()
    data = json.loads(baseline_file.read_text(encoding="utf-8"))
    assert "median_ms" in data
