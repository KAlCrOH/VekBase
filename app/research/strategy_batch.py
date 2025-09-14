# ============================================================
# Context Banner — strategy_batch | Category: research
# Purpose: Batch-Ausführung einfacher Strategien über Parameter-Grids & Seeds zur Robustheitsanalyse.
#
# Contracts
#   Interface: Strategy (protocol-like) requires .name, .generate_trades(price_series, params, seed) -> List[Trade]
#   Function: run_strategy_batch(strategies, price_series, param_grid, seeds, failure_dd_threshold) -> (results, summary)
#   Output: results list of dicts (strategy, param_hash, params, seed, metrics), summary dict with robustness metrics.
#   Determinism: Provided price_series, params, seed → deterministic outputs.
#
# Metrics
#   robust_cagr_median, robust_cagr_p05, robust_cagr_p95 based on per-run CAGR (using realized equity curve vs cost basis 0 start)
#   failure_rate: Anteil Runs mit max_drawdown_realized > failure_dd_threshold
#   param_sensitivity_score: stddev of CAGR grouped by parameter set distance heuristic (simple numeric diff ratio)
#
# Feature Flag (planned integration): VEK_STRAT_SWEEP (not enforced here to keep pure library).
#
# Dependencies
#   Internal: analytics.metrics.aggregate_metrics
#   External: stdlib only
# ============================================================
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Callable, Sequence
from datetime import datetime, UTC, timedelta
import hashlib
import math
import random

from ..core.trade_model import Trade
from ..analytics.metrics import aggregate_metrics


@dataclass
class StrategyResult:
    strategy: str
    param_hash: str
    params: Dict[str, Any]
    seed: int
    metrics: Dict[str, Any]


class Strategy:
    name: str
    def generate_trades(self, price_series: List[float], params: Dict[str, Any], seed: int) -> List[Trade]:  # pragma: no cover (interface)
        raise NotImplementedError


class MovingAverageCrossover(Strategy):
    """Very simple MA crossover: BUY when short MA crosses above long MA, SELL when below; flat-only position management (no scaling)."""
    name = "ma_crossover"
    def generate_trades(self, price_series: List[float], params: Dict[str, Any], seed: int) -> List[Trade]:
        short = int(params.get("ma_short", 5))
        long = int(params.get("ma_long", 20))
        if short >= long:
            raise ValueError("ma_short must be < ma_long")
        trades: List[Trade] = []
        position = 0
        trade_counter = 0
        for i in range(long, len(price_series)):
            window_short = price_series[i-short:i]
            window_long = price_series[i-long:i]
            ma_s = sum(window_short)/len(window_short)
            ma_l = sum(window_long)/len(window_long)
            ts = datetime(2025,1,1, tzinfo=UTC) + timedelta(minutes=i)
            price = price_series[i]
            if position == 0 and ma_s > ma_l:
                # enter
                trades.append(Trade(trade_id=f"t{trade_counter}", ts=ts, ticker="SIM", action="BUY", shares=1, price=price, fees=0.0))
                position = 1
                trade_counter += 1
            elif position == 1 and ma_s < ma_l:
                # exit
                trades.append(Trade(trade_id=f"t{trade_counter}", ts=ts, ticker="SIM", action="SELL", shares=1, price=price, fees=0.0))
                position = 0
                trade_counter += 1
        # force close end if open
        if position == 1:
            ts = datetime(2025,1,1, tzinfo=UTC) + timedelta(minutes=len(price_series))
            trades.append(Trade(trade_id=f"t{trade_counter}", ts=ts, ticker="SIM", action="SELL", shares=1, price=price_series[-1], fees=0.0))
        return trades


class RandomFlip(Strategy):
    """Random flip strategy for baseline dispersion: flips position on random trigger probability."""
    name = "random_flip"
    def generate_trades(self, price_series: List[float], params: Dict[str, Any], seed: int) -> List[Trade]:
        rng = random.Random(seed)
        p = float(params.get("flip_prob", 0.05))
        trades: List[Trade] = []
        position = 0
        trade_counter = 0
        for i, price in enumerate(price_series):
            ts = datetime(2025,1,2, tzinfo=UTC) + timedelta(minutes=i)
            if position == 0 and rng.random() < p:
                trades.append(Trade(trade_id=f"rf{trade_counter}", ts=ts, ticker="SIM", action="BUY", shares=1, price=price, fees=0.0))
                position = 1
                trade_counter += 1
            elif position == 1 and rng.random() < p:
                trades.append(Trade(trade_id=f"rf{trade_counter}", ts=ts, ticker="SIM", action="SELL", shares=1, price=price, fees=0.0))
                position = 0
                trade_counter += 1
        if position == 1:
            trades.append(Trade(trade_id=f"rf{trade_counter}", ts=datetime(2025,1,2, tzinfo=UTC) + timedelta(minutes=len(price_series)), ticker="SIM", action="SELL", shares=1, price=price_series[-1], fees=0.0))
        return trades


def _param_hash(params: Dict[str, Any]) -> str:
    items = sorted(params.items())
    raw = "|".join(f"{k}={v}" for k,v in items)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def _compute_cagr(trades: List[Trade]) -> float:
    # Reuse aggregate_metrics realized curve logic via realized equity metrics
    if not trades:
        return 0.0
    metrics = aggregate_metrics(trades)
    return float(metrics.get("cagr", 0.0))


def run_strategy_batch(
    strategies: Sequence[Strategy],
    price_series: List[float],
    param_grid: Dict[str, List[Any]],
    seeds: Sequence[int],
    failure_dd_threshold: float = 0.3,  # 30% drawdown threshold for failure_rate
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run all strategies across cartesian product of param_grid & seeds.
    param_grid: dict parameter_name -> list[values]. All strategies share grid (simple first version).
    Returns (results, summary).
    """
    # build param combinations
    keys = list(param_grid.keys())
    combos: List[Dict[str, Any]] = []
    def _recurse(idx: int, cur: Dict[str, Any]):
        if idx == len(keys):
            combos.append(dict(cur))
            return
        k = keys[idx]
        for v in param_grid[k]:
            cur[k] = v
            _recurse(idx+1, cur)
    _recurse(0, {})
    results: List[Dict[str, Any]] = []
    cagr_values: List[float] = []
    dd_values: List[float] = []
    # iterate
    for strat in strategies:
        for combo in combos:
            ph = _param_hash(combo)
            for seed in seeds:
                trades = strat.generate_trades(price_series, combo, seed)
                metrics = aggregate_metrics(trades)
                cagr_raw = float(metrics.get("cagr", 0.0))
                # Sanitize CAGR to avoid infinities / extreme explosions over very short horizons
                if not math.isfinite(cagr_raw):
                    cagr = 0.0
                else:
                    # Hard clamp to reasonable research bound to keep variance finite
                    if cagr_raw > 1e6:
                        cagr = 1e6
                    elif cagr_raw < -1e6:
                        cagr = -1e6
                    else:
                        cagr = cagr_raw
                dd = float(metrics.get("max_drawdown_realized", 0.0))
                cagr_values.append(cagr)
                dd_values.append(dd)
                results.append({
                    "strategy": strat.name,
                    "param_hash": ph,
                    "params": combo,
                    "seed": seed,
                    "metrics": {"cagr": cagr, "max_drawdown_realized": dd},
                })
    if not results:
        return [], {"robust_cagr_median": 0.0, "robust_cagr_p05": 0.0, "robust_cagr_p95": 0.0, "failure_rate": 0.0, "param_sensitivity_score": 0.0, "runs": 0}
    sorted_cagr = sorted(cagr_values)
    def _q(vals: List[float], q: float) -> float:
        if not vals: return 0.0
        if q<=0: return vals[0]
        if q>=1: return vals[-1]
        pos = (len(vals)-1)*q
        lo = int(pos); hi = min(lo+1, len(vals)-1)
        frac = pos - lo
        return vals[lo]*(1-frac) + vals[hi]*frac
    robust_cagr_median = _q(sorted_cagr, 0.5)
    robust_cagr_p05 = _q(sorted_cagr, 0.05)
    robust_cagr_p95 = _q(sorted_cagr, 0.95)
    failures = sum(1 for d in dd_values if d > failure_dd_threshold)
    failure_rate = failures / len(dd_values)
    # simplistic param sensitivity: stddev of cagr over unique param hashes (if only one => 0)
    by_param_hash: Dict[str, List[float]] = {}
    for r in results:
        by_param_hash.setdefault(r["param_hash"], []).append(r["metrics"]["cagr"])
    # average variance across param groups vs global variance
    global_mean = sum(cagr_values)/len(cagr_values)
    global_var = sum((x-global_mean)**2 for x in cagr_values)/len(cagr_values) if cagr_values else 0.0
    group_means = [sum(v)/len(v) for v in by_param_hash.values()]
    group_var = sum((m-global_mean)**2 for m in group_means)/len(group_means) if group_means else 0.0
    param_sensitivity_score = group_var ** 0.5 if len(group_means) > 1 else 0.0
    summary = {
        "robust_cagr_median": robust_cagr_median,
        "robust_cagr_p05": robust_cagr_p05,
        "robust_cagr_p95": robust_cagr_p95,
        "failure_rate": failure_rate,
        "param_sensitivity_score": param_sensitivity_score,
        "runs": len(results),
        "param_combinations": len(combos),
        "strategies": [s.name for s in strategies],
    }
    return results, summary
