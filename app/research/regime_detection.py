# ============================================================
# Context Banner — regime_detection | Category: research
# Purpose: Lightweight market regime labeling (volatility + trend) and performance summarization by regime.
#
# Contracts
#   compute_regime_labels(price_series, window_vol=20, window_trend=20, vol_quantiles=(0.33,0.66)) -> List[dict]
#     Returns list of dicts: {"idx": i, "price": p, "vol": rolling_vol, "vol_bucket": str, "trend_slope": slope, "trend_bucket": str}
#   summarize_regime_returns(trades, regime_labels) -> Dict[str, Any]
#     Maps realized equity increments into regime buckets, computing per-bucket summary (cagr, total_pnl, count).
#
# Determinism: Pure functions given inputs (no external randomness).
# Dependencies: analytics.metrics.aggregate_metrics (indirect via realized pnl computation logic replicated minimally for efficiency).
# ============================================================
from __future__ import annotations
from typing import List, Dict, Any, Sequence, Tuple
from math import sqrt
from statistics import mean
from ..core.trade_model import Trade
from ..analytics.metrics import compute_realized_pnl, realized_equity_curve


def _rolling_vol(prices: Sequence[float], window: int) -> List[float]:
    if window <= 1:
        return [0.0]*len(prices)
    out: List[float] = []
    for i in range(len(prices)):
        if i < window:
            out.append(0.0)
            continue
        window_slice = prices[i-window+1:i+1]
        m = sum(window_slice)/len(window_slice)
        var = sum((x-m)**2 for x in window_slice)/len(window_slice)
        out.append(sqrt(var))
    return out


def _rolling_trend_slope(prices: Sequence[float], window: int) -> List[float]:
    # Simple linear regression slope (x=0..window-1) over last window; if insufficient window -> 0
    if window <= 1:
        return [0.0]*len(prices)
    out: List[float] = []
    denom = window*(window-1)/2  # sum x
    sum_x2 = sum(i*i for i in range(window))
    denom_lr = window*sum_x2 - (window*(window-1)/2)**2
    if denom_lr == 0:
        denom_lr = 1.0
    for i in range(len(prices)):
        if i < window:
            out.append(0.0)
            continue
        window_slice = prices[i-window+1:i+1]
        # compute slope y ~ a + b x; x=0..w-1
        sum_y = sum(window_slice)
        sum_xy = sum(j*window_slice[j] for j in range(window))
        b = (window*sum_xy - (window*(window-1)/2)*sum_y)/denom_lr
        out.append(b)
    return out


def compute_regime_labels(
    price_series: Sequence[float],
    window_vol: int = 20,
    window_trend: int = 20,
    vol_quantiles: Tuple[float, float] = (0.33, 0.66),
    trend_thresh: float | None = None,
) -> List[Dict[str, Any]]:
    """Return regime labels combining rolling volatility bucket and trend slope bucket.
    vol buckets: low/mid/high based on provided quantiles over non-zero vol observations.
    trend buckets: down/flat/up based on slope thresholds. If trend_thresh None -> compute as median(|slope|) of non-zero slopes.
    """
    if not price_series:
        return []
    vols = _rolling_vol(price_series, window_vol)
    slopes = _rolling_trend_slope(price_series, window_trend)
    nonzero_vols = sorted(v for v in vols if v > 0)
    def _q(vals: List[float], q: float) -> float:
        if not vals:
            return 0.0
        if q <= 0: return vals[0]
        if q >= 1: return vals[-1]
        pos = (len(vals)-1)*q
        lo = int(pos); hi = min(lo+1, len(vals)-1)
        frac = pos - lo
        return vals[lo]*(1-frac) + vals[hi]*frac
    if nonzero_vols:
        q1 = _q(nonzero_vols, vol_quantiles[0])
        q2 = _q(nonzero_vols, vol_quantiles[1])
    else:
        q1 = q2 = 0.0
    abs_slopes = [abs(s) for s in slopes if s != 0]
    if trend_thresh is None:
        trend_thresh = _q(sorted(abs_slopes), 0.5) if abs_slopes else 0.0
    labels: List[Dict[str, Any]] = []
    for i, p in enumerate(price_series):
        v = vols[i]
        s = slopes[i]
        if v == 0 or q2 == 0:
            vol_bucket = "mid"  # insufficient data treat neutral
        elif v < q1:
            vol_bucket = "low"
        elif v < q2:
            vol_bucket = "mid"
        else:
            vol_bucket = "high"
        # Treat equality as directional (prevents all 'flat' if constant slope matches threshold)
        if trend_thresh == 0:
            trend_bucket = "flat"
        else:
            if s >= trend_thresh:
                trend_bucket = "up"
            elif s <= -trend_thresh:
                trend_bucket = "down"
            else:
                trend_bucket = "flat"
        labels.append({
            "idx": i,
            "price": p,
            "vol": v,
            "vol_bucket": vol_bucket,
            "trend_slope": s,
            "trend_bucket": trend_bucket,
        })
    return labels


def summarize_regime_returns(trades: List[Trade], regime_labels: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize realized equity increments by (vol_bucket, trend_bucket) regime.
    Approach: Build realized equity curve, map each point to the regime label at nearest index, compute per-regime stats.
    Returns dict with keys:
      - regimes: list of {vol_bucket, trend_bucket, total_pnl, observations, avg_increment}
      - global: {total_pnl, points}
    Notes: Equity curve uses realized cumulative PnL; increments are diffs between successive points.
    """
    curve = realized_equity_curve(trades)
    if not curve or not regime_labels:
        return {"regimes": [], "global": {"total_pnl": 0.0, "points": 0}}
    increments: List[float] = []
    for i in range(1, len(curve)):
        increments.append(curve[i][1] - curve[i-1][1])
    # Map curve points to regime idx proportionally along price_series length
    max_idx = max(l["idx"] for l in regime_labels)
    # Use linear mapping of curve position to index in price series
    def _map_point(i_point: int) -> Dict[str, Any]:
        if max_idx <= 0:
            return regime_labels[0]
        # clamp
        est_idx = int((i_point / (len(curve)-1)) * max_idx)
        if est_idx < 0: est_idx = 0
        if est_idx > max_idx: est_idx = max_idx
        return regime_labels[est_idx]
    per_bucket: Dict[Tuple[str,str], List[float]] = {}
    for i_inc, inc in enumerate(increments, start=1):  # increment belongs to segment ending at point i_inc
        lbl = _map_point(i_inc)
        key = (lbl["vol_bucket"], lbl["trend_bucket"])
        per_bucket.setdefault(key, []).append(inc)
    regimes_out: List[Dict[str, Any]] = []
    for (vb, tb), vals in sorted(per_bucket.items()):
        total = sum(vals)
        regimes_out.append({
            "vol_bucket": vb,
            "trend_bucket": tb,
            "total_pnl": total,
            "observations": len(vals),
            "avg_increment": (total/len(vals)) if vals else 0.0,
        })
    return {
        "regimes": regimes_out,
        "global": {"total_pnl": curve[-1][1], "points": len(curve)},
    }
