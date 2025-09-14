"""regime_ui — UI-facing helpers for regime detection overlay & summary (Analytics Tab),
feature-flag gated by `VEK_REGIME`.

Contracts:
    prepare_regime_labels(prices: list[float]) -> list[dict]
    summarize_regimes(trades, prices) -> dict {labels: [...], summary: {...}} or {error: str}
    compute_overlay_segments(labels) -> compressed contiguous segments.

Design:
    - Pure functions, deterministic.
    - No side effects / I/O.
    - Gracefully handle short or empty price series.

Tests: tests/test_regime_ui.py
"""
from __future__ import annotations
from typing import List, Dict, Any, Sequence
from app.research.regime_detection import compute_regime_labels


def prepare_regime_labels(prices: Sequence[float]) -> List[Dict[str, Any]]:
    if not prices or len(prices) < 8:
        return []
    # Adaptive windows: smaller for short series
    win = max(5, min(20, len(prices)//4))
    return compute_regime_labels(prices, window_vol=win, window_trend=win)


def summarize_regimes(trades, prices: Sequence[float]) -> Dict[str, Any]:
    labels = prepare_regime_labels(prices)
    if not labels:
        return {"labels": [], "summary": {"regimes": [], "global": {"total_pnl": 0.0, "points": 0}}}
    try:
        # summarize_regime_returns expects realized equity mapping; trades may be empty
        from app.research.regime_detection import summarize_regime_returns as _summ
        summ = _summ(trades, labels)
    except Exception as e:
        return {"error": f"summary error: {e}"}
    return {"labels": labels, "summary": summ}


def compute_overlay_segments(labels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not labels:
        return []
    segs: List[Dict[str, Any]] = []
    cur = None
    for lbl in labels:
        key = (lbl['vol_bucket'], lbl['trend_bucket'])
        if cur is None:
            cur = {"start_idx": lbl['idx'], "end_idx": lbl['idx'], "vol_bucket": key[0], "trend_bucket": key[1]}
        else:
            if cur['vol_bucket'] == key[0] and cur['trend_bucket'] == key[1]:
                cur['end_idx'] = lbl['idx']
            else:
                segs.append(cur)
                cur = {"start_idx": lbl['idx'], "end_idx": lbl['idx'], "vol_bucket": key[0], "trend_bucket": key[1]}
    if cur:
        segs.append(cur)
    return segs

__all__ = ["prepare_regime_labels", "summarize_regimes", "compute_overlay_segments"]
