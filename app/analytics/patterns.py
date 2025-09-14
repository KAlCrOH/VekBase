"""
# ============================================================
# Context Banner — patterns | Category: analytics
# Purpose: Erste Pattern Analytics Stubs (Histogram Holding-Dauer, Scatter EntryPrice vs Realized Return)

# Contracts
#   Functions:
#     holding_duration_histogram(trades) -> List[int] bucket counts (fixed bucket size in minutes)
#     entry_return_scatter(trades) -> List[tuple(entry_price, realized_return_perc)]
#   Inputs: List[Trade]
#   Outputs: Reine In-Memory Strukturen für UI Visualisierung.
#   Side-Effects: none
#   Determinism: deterministic (sort by ts)

# Invariants
#   - Keine Datei-/Netzwerkzugriffe
#   - Nur realized Returns für SELL Events

# Dependencies
#   Internal: core.trade_model.Trade
#   External: stdlib

# Tests
#   tests/test_metrics.py (bereits PnL), neue tests/test_patterns.py für Stubs

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from __future__ import annotations
from typing import List, Tuple, Dict
from datetime import datetime
from ..core.trade_model import Trade


def holding_duration_histogram(trades: List[Trade], bucket_minutes: int = 60, max_buckets: int = 10) -> Dict[str, object]:
    """Compute holding duration histogram and basic stats.
    Returns dict: {'buckets': List[int], 'bucket_minutes': int, 'p50': float, 'p90': float, 'p95': float,
                   'overflow_count': int, 'count': int}
    overflow_count counts portions whose duration exceed last bucket upper bound.
    """
    if bucket_minutes <= 0:
        raise ValueError("bucket_minutes must be >0")
    inv: List[Tuple[float, float, datetime]] = []  # shares, price, ts
    buckets = [0 for _ in range(max_buckets)]
    overflow = 0
    durations: List[float] = []
    for t in sorted(trades, key=lambda x: x.ts):
        if t.action == "BUY":
            inv.append((t.shares, t.price, t.ts))
        else:  # SELL
            remaining = t.shares
            i = 0
            while remaining > 1e-12 and i < len(inv):
                lot_sh, lot_price, lot_ts = inv[i]
                take = min(lot_sh, remaining)
                dur_min = (t.ts - lot_ts).total_seconds() / 60.0
                durations.append(dur_min)
                bucket_idx = int(dur_min // bucket_minutes)
                if bucket_idx >= max_buckets:
                    overflow += 1
                else:
                    buckets[bucket_idx] += 1
                lot_sh -= take
                remaining -= take
                if lot_sh <= 1e-12:
                    inv.pop(i)
                else:
                    inv[i] = (lot_sh, lot_price, lot_ts)
                    i += 1
    def _percentile(vals: List[float], pct: float) -> float:
        if not vals:
            return 0.0
        s = sorted(vals)
        idx = int((len(s)-1) * pct)
        return s[idx]
    return {
        'buckets': buckets,
        'bucket_minutes': bucket_minutes,
        'p50': _percentile(durations, 0.5),
        'p90': _percentile(durations, 0.9),
        'p95': _percentile(durations, 0.95),
        'overflow_count': overflow,
        'count': len(durations),
    }


def entry_return_scatter(trades: List[Trade]) -> List[Tuple[float, float]]:
    """Return list of (entry_price, realized_return_percent) for each SELL match (portion-wise)."""
    inv: List[Tuple[float, float]] = []  # shares, price
    points: List[Tuple[float, float]] = []
    for t in sorted(trades, key=lambda x: x.ts):
        if t.action == "BUY":
            inv.append((t.shares, t.price))
        else:
            remaining = t.shares
            i = 0
            while remaining > 1e-12 and i < len(inv):
                lot_sh, lot_price = inv[i]
                take = min(lot_sh, remaining)
                ret_pct = ((t.price - lot_price) / lot_price) if lot_price > 0 else 0.0
                points.append((lot_price, ret_pct))
                lot_sh -= take
                remaining -= take
                if lot_sh <= 1e-12:
                    inv.pop(i)
                else:
                    inv[i] = (lot_sh, lot_price)
                    i += 1
    return points


def return_distribution(trades: List[Trade], bucket_size: float = 0.01, max_buckets: int = 200) -> Dict[str, object]:
    """Compute histogram of realized returns (portion-wise) from SELL matches.
    Returns dict: {'buckets': [...], 'bucket_size': float, 'count': int, 'tail_left_count': int, 'tail_right_count': int,
                   'p90': float, 'p95': float}
    Buckets centered at 0 start from negative to positive based on observed min/max clipped to max_buckets.
    tail_left/right_count: portions beyond first/last bucket after clipping.
    """
    if bucket_size <= 0:
        raise ValueError("bucket_size must be >0")
    inv: List[Tuple[float, float]] = []
    rets: List[float] = []
    for t in sorted(trades, key=lambda x: x.ts):
        if t.action == "BUY":
            inv.append((t.shares, t.price))
        else:
            remaining = t.shares
            i = 0
            while remaining > 1e-12 and i < len(inv):
                lot_sh, lot_price = inv[i]
                take = min(lot_sh, remaining)
                if lot_price > 0:
                    rets.append((t.price - lot_price) / lot_price)
                lot_sh -= take
                remaining -= take
                if lot_sh <= 1e-12:
                    inv.pop(i)
                else:
                    inv[i] = (lot_sh, lot_price)
                    i += 1
    if not rets:
        return {'buckets': [], 'bucket_size': bucket_size, 'count': 0, 'tail_left_count': 0, 'tail_right_count': 0, 'p90': 0.0, 'p95': 0.0}
    mn, mx = min(rets), max(rets)
    # Determine bucket range symmetrical around 0 for consistency
    bound = max(abs(mn), abs(mx))
    bucket_count_each_side = int(bound / bucket_size) + 1
    total_possible = bucket_count_each_side * 2
    if total_possible > max_buckets:
        # increase bucket_size to fit in max_buckets
        scale = total_possible / max_buckets
        bucket_size *= scale
        bucket_count_each_side = int(bound / bucket_size) + 1
    start = -bucket_count_each_side * bucket_size
    buckets: List[Dict[str, object]] = []
    counts: Dict[int, int] = {}
    tail_left = 0
    tail_right = 0
    for r in rets:
        idx = int((r - start) // bucket_size)
        if idx < 0:
            tail_left += 1
            continue
        if idx > (int(((bucket_count_each_side * 2) * bucket_size) / bucket_size) + 2):  # safety
            tail_right += 1
            continue
        counts[idx] = counts.get(idx, 0) + 1
    total_buckets = bucket_count_each_side * 2 + 1
    for i in range(total_buckets):
        b_start = start + i * bucket_size
        buckets.append({'start': round(b_start,6), 'end': round(b_start + bucket_size,6), 'count': counts.get(i,0)})
    def _percentile(vals: List[float], pct: float) -> float:
        if not vals:
            return 0.0
        s = sorted(vals)
        idx = int((len(s)-1) * pct)
        return s[idx]
    return {
        'buckets': buckets,
        'bucket_size': bucket_size,
        'count': len(rets),
        'tail_left_count': tail_left,
        'tail_right_count': tail_right,
        'p90': _percentile(rets, 0.9),
        'p95': _percentile(rets, 0.95),
    }
