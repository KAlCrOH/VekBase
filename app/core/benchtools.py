"""
# ============================================================
# Context Banner — benchtools | Category: core
# Purpose: Einfache lokale Benchmark-Harness für ausgewählte Funktionen (Analytics/Simulation) mit Baseline-Persistenz.

# Contracts
#   run_benchmark(target: str, repeat: int = 3) -> BenchmarkResult
#       - target: Schlüssel einer registrierten Benchmarkfunktion (siehe REGISTRY)
#       - repeat: Anzahl Wiederholungen; median wird als repräsentativer Wert genommen
#       - Persistenz: legt/aktualisiert JSON Baseline unter data/devtools/bench_<target>.json
#   get_registry() -> dict[str,str]: Liefert Mapping target->Beschreibung

# BenchmarkResult Felder:
#   target, runs (List[float ms]), median_ms, baseline_ms (oder None), delta_pct (oder None), faster (bool|None)

# Invariants
#   - Keine Netzwerkzugriffe
#   - Reproduzierbar (Funktion selbst muss deterministisch sein; harness misst Zeit via perf_counter)
#   - Additiv; keine Änderungen an getesteten Funktionen

# Dependencies
#   Internal: analytics.metrics (aggregate_metrics, realized_equity_curve)
#   External: stdlib only

# Tests
#   tests/test_benchtools.py (Happy + Baseline Persistenz)

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from time import perf_counter
from statistics import median
from pathlib import Path
import json
from typing import Callable, Dict, List

from .trade_repo import TradeRepository
from .trade_model import validate_trade_dict
from ..analytics.metrics import aggregate_metrics, realized_equity_curve


def _sample_trades_repo() -> TradeRepository:
    repo = TradeRepository()
    sample = [
        {"trade_id":"b1","ts":"2024-01-01T09:00:00","ticker":"ABC","action":"BUY","shares":10,"price":10,"fees":0},
        {"trade_id":"b2","ts":"2024-01-02T09:00:00","ticker":"ABC","action":"BUY","shares":5,"price":12,"fees":0},
        {"trade_id":"s1","ts":"2024-01-03T09:00:00","ticker":"ABC","action":"SELL","shares":8,"price":15,"fees":1},
        {"trade_id":"s2","ts":"2024-01-04T09:00:00","ticker":"ABC","action":"SELL","shares":7,"price":16,"fees":1},
    ]
    for r in sample:
        repo.add_trade(validate_trade_dict(r))
    return repo


def _bench_aggregate_metrics():
    repo = _sample_trades_repo()
    return aggregate_metrics(repo.all())


def _bench_realized_equity_curve():
    repo = _sample_trades_repo()
    return realized_equity_curve(repo.all())


REGISTRY: Dict[str, tuple[Callable[[], object], str]] = {
    "aggregate_metrics": (_bench_aggregate_metrics, "Aggregate realized/unrealized metrics (sample trades)"),
    "realized_equity_curve": (_bench_realized_equity_curve, "Compute realized equity curve (sample trades)"),
}


@dataclass
class BenchmarkResult:
    target: str
    runs_ms: List[float]
    median_ms: float
    baseline_ms: float | None
    delta_pct: float | None
    faster: bool | None  # True wenn schneller als baseline (>1% Unterschied), False wenn langsamer, None wenn keine baseline

    def to_dict(self) -> dict:
        return asdict(self)


def get_registry() -> Dict[str, str]:
    return {k: v[1] for k, v in REGISTRY.items()}


def run_benchmark(target: str, repeat: int = 3, persist: bool = True) -> BenchmarkResult:
    if target not in REGISTRY:
        raise ValueError(f"Unknown benchmark target: {target}")
    func, _desc = REGISTRY[target]
    if repeat < 1:
        raise ValueError("repeat must be >=1")
    runs: List[float] = []
    for _ in range(repeat):
        t0 = perf_counter()
        func()  # ignore returned value for timing
        dt_ms = (perf_counter() - t0) * 1000.0
        runs.append(dt_ms)
    med = median(runs)
    baseline_path = Path("data/devtools")
    baseline_path.mkdir(parents=True, exist_ok=True)
    baseline_file = baseline_path / f"bench_{target}.json"
    baseline_ms: float | None = None
    if baseline_file.exists():
        try:
            existing = json.loads(baseline_file.read_text(encoding="utf-8"))
            baseline_ms = float(existing.get("median_ms"))
        except Exception:
            baseline_ms = None
    delta_pct: float | None = None
    faster: bool | None = None
    if baseline_ms is not None and baseline_ms > 0:
        delta_pct = (med - baseline_ms) / baseline_ms * 100.0
        if abs(delta_pct) > 1.0:  # threshold
            faster = med < baseline_ms
    if persist:
        out = {"target": target, "median_ms": med, "runs_ms": runs}
        baseline_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return BenchmarkResult(target=target, runs_ms=runs, median_ms=med, baseline_ms=baseline_ms, delta_pct=delta_pct, faster=faster)
