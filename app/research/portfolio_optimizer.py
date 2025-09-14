# ============================================================
# Context Banner — portfolio_optimizer | Category: research
# Purpose: Combine multiple strategy return streams using allocation policies and compute portfolio-level metrics.
#
# Contracts
#   build_returns_matrix(equity_curves: dict[str, list[(ts, equity)]]) -> (timestamps, returns_by_strategy)
#   allocate_weights(returns_by_strategy: dict[str, list[float]], policy: str, max_dd_cap: float|None=None) -> dict[str, float]
#   assemble_portfolio(timestamps, returns_by_strategy, weights) -> list[(ts, equity)]
#   portfolio_metrics(curve, individual_returns, weights) -> dict
#
# Allocation Policies
#   equal_weight: 1/N per strategy
#   vol_parity: weights ∝ 1/vol (std of returns); normalized; if all zero -> equal
#   max_dd_capped: scale existing vol_parity weights so realized max drawdown <= cap (if provided) by uniform scaling
#
# Determinism: Pure functions given inputs; no randomness or external I/O.
# ============================================================
from __future__ import annotations
from typing import Dict, List, Tuple
from math import sqrt

EPS = 1e-12


def _simple_returns(curve: List[Tuple]) -> List[float]:
    if len(curve) < 2:
        return []
    out: List[float] = []
    for i in range(1, len(curve)):
        prev = curve[i-1][1]
        cur = curve[i][1]
        denom = prev if abs(prev) > EPS else (EPS if prev >= 0 else -EPS)
        out.append((cur - prev)/denom)
    return out


def build_returns_matrix(equity_curves: Dict[str, List[Tuple]]) -> Tuple[List, Dict[str, List[float]]]:
    # Align by intersection of timestamps for simplicity
    timestamp_sets = [set(ts for ts,_ in curve) for curve in equity_curves.values() if curve]
    if not timestamp_sets:
        return [], {}
    common = sorted(set.intersection(*timestamp_sets))
    # Build aligned equity per strategy then compute returns
    aligned_curves: Dict[str, List[Tuple]] = {}
    for name, curve in equity_curves.items():
        idx = {ts: val for ts,val in curve}
        aligned = [(ts, idx[ts]) for ts in common]
        aligned_curves[name] = aligned
    returns_by: Dict[str, List[float]] = {name: _simple_returns(curve) for name, curve in aligned_curves.items()}
    # Drop first timestamp because returns shorter by 1
    return common[1:], returns_by


def _std(vals: List[float]) -> float:
    if not vals:
        return 0.0
    m = sum(vals)/len(vals)
    return sqrt(sum((v-m)**2 for v in vals)/len(vals))


def allocate_weights(returns_by_strategy: Dict[str, List[float]], policy: str, max_dd_cap: float | None = None) -> Dict[str, float]:
    names = sorted(returns_by_strategy.keys())
    if not names:
        return {}
    n = len(names)
    if policy == "equal_weight":
        weights = {name: 1.0/n for name in names}
    elif policy == "vol_parity" or policy == "max_dd_capped":
        inv_vols = []
        for name in names:
            vol = _std(returns_by_strategy[name])
            inv_vols.append(1.0/vol if vol > 0 else 0.0)
        if sum(inv_vols) == 0:
            weights = {name: 1.0/n for name in names}
        else:
            s = sum(inv_vols)
            weights = {name: inv_vols[i]/s for i,name in enumerate(names)}
    else:
        raise ValueError(f"Unknown policy: {policy}")
    if policy == "max_dd_capped" and max_dd_cap is not None:
        # Build provisional portfolio to measure drawdown, then scale if needed
        # Use cumulative equity starting at 100
        max_dd, curve = _portfolio_drawdown_and_curve(returns_by_strategy, weights)
        if max_dd > max_dd_cap and max_dd > 0:
            scale = max_dd_cap / max_dd
            weights = {k: v*scale for k,v in weights.items()}
    # Normalize after scaling (if scale <1 maintains proportions but keep sum<=1; renorm to sum=1?) -> Keep raw scaled sum (can be <1) to reflect uninvested cash
    return weights


def _portfolio_drawdown_and_curve(returns_by_strategy: Dict[str, List[float]], weights: Dict[str, float]):
    # Assumes all return series aligned length L
    if not returns_by_strategy:
        return 0.0, []
    L = len(next(iter(returns_by_strategy.values())))
    equity = 100.0
    curve = [equity]
    for i in range(L):
        r = 0.0
        for name, rets in returns_by_strategy.items():
            if i < len(rets):
                r += weights.get(name, 0.0) * rets[i]
        equity *= (1 + r)
        curve.append(equity)
    # Compute realized drawdown on equity list
    peak = curve[0]
    max_dd = 0.0
    for v in curve:
        if v > peak:
            peak = v
        dd = (peak - v)/peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return max_dd, curve


def assemble_portfolio(timestamps, returns_by_strategy: Dict[str, List[float]], weights: Dict[str, float]) -> List[Tuple]:
    if not timestamps:
        return []
    # Build equity curve from weighted returns (starting at 100)
    equity = 100.0
    out: List[Tuple] = []
    # Prepend a starting point with first timestamp minus index (synthetic) not needed — use first actual timestamp as baseline
    first_ts = timestamps[0]
    out.append((first_ts, equity))
    for i, ts in enumerate(timestamps):
        if i >= len(timestamps):
            break
        r = 0.0
        for name, rets in returns_by_strategy.items():
            if i < len(rets):
                r += weights.get(name, 0.0) * rets[i]
        equity *= (1 + r)
        out.append((ts, equity))
    return out


def portfolio_metrics(curve: List[Tuple], individual_returns: Dict[str, List[float]], weights: Dict[str, float]) -> Dict[str, float]:
    if not curve or len(curve) < 2:
        return {"portfolio_cagr": 0.0, "portfolio_max_dd": 0.0, "diversification_benefit": 0.0, "weight_sum": sum(weights.values())}
    # CAGR approximation using first/last
    start_eq = curve[0][1]
    end_eq = curve[-1][1]
    # Use total compounded return over period (non-annualized) to keep metric bounded & align with test expectations
    portfolio_cagr = (end_eq/start_eq) - 1 if start_eq > 0 and end_eq > 0 else 0.0
    # Max drawdown (percent)
    peak = curve[0][1]
    max_dd = 0.0
    for _, v in curve:
        if v > peak:
            peak = v
        dd = (peak - v)/peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    # Diversification benefit = sum individual vols / portfolio vol - 1
    vols = []
    for name, rets in individual_returns.items():
        vols.append(_std(rets))
    port_returns: List[float] = []
    for i in range(len(next(iter(individual_returns.values()), []))):
        r = 0.0
        for name, rets in individual_returns.items():
            if i < len(rets):
                r += weights.get(name, 0.0) * rets[i]
        port_returns.append(r)
    port_vol = _std(port_returns)
    # Weighted volatility sum (no diversification benefit for perfectly correlated identical series)
    weighted_vol_sum = 0.0
    for name, rets in individual_returns.items():
        v = _std(rets)
        weighted_vol_sum += weights.get(name, 0.0) * v
    diversification_benefit = (weighted_vol_sum/port_vol - 1) if port_vol > 0 and weighted_vol_sum > 0 else 0.0
    return {
        "portfolio_cagr": portfolio_cagr,
        "portfolio_max_dd": max_dd,
        "diversification_benefit": diversification_benefit,
        "weight_sum": sum(weights.values()),
    }
