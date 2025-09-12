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
from typing import List, Tuple
from datetime import datetime
from ..core.trade_model import Trade


def holding_duration_histogram(trades: List[Trade], bucket_minutes: int = 60, max_buckets: int = 10) -> List[int]:
    """Compute simplistic histogram of holding durations (BUY->portion of SELL).
    Approach: FIFO match similar to realized pnl but only aggregate durations into buckets.
    """
    if bucket_minutes <= 0:
        raise ValueError("bucket_minutes must be >0")
    inv: List[Tuple[float, float, datetime]] = []  # shares, price, ts
    buckets = [0 for _ in range(max_buckets)]
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
                bucket_idx = int(dur_min // bucket_minutes)
                if bucket_idx >= max_buckets:
                    bucket_idx = max_buckets - 1
                buckets[bucket_idx] += 1
                lot_sh -= take
                remaining -= take
                if lot_sh <= 1e-12:
                    inv.pop(i)
                else:
                    inv[i] = (lot_sh, lot_price, lot_ts)
                    i += 1
    return buckets


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
