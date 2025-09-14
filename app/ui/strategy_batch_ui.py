"""
# ============================================================
# Context Banner — strategy_batch_ui | Category: ui
# Purpose: Thin UI-facing helper to safely invoke research.strategy_batch.run_strategy_batch with
#          JSON-derived user inputs (strategies list, param grid, seeds) for the Strategy Batch Panel.
#
# Contracts
#   run_strategy_batch_ui(strategies_json:str, param_grid_json:str, seeds_csv:str, price_series:list[float]|None) -> dict
#     - Parses user JSON/CSV inputs; on parse/validation error returns {error:<msg>} (no exception to UI layer)
#     - If price_series is None -> uses synthetic deterministic price series (length 120) for preview value
#   Outputs: dict { summary: {...}, results: [...], error: optional }
#   Determinism: Synthetic series deterministic; underlying run_strategy_batch is deterministic given inputs.
#
# Invariants
#   - No external dependencies; stdlib only.
#   - No file I/O / network.
#   - Feature flag gating handled by console UI (VEK_STRAT_SWEEP) – this module is inert when not imported.
#
# Dependencies
#   Internal: app.research.strategy_batch
#   External: stdlib json
#
# Tests
#   tests/test_strategy_batch_ui.py (happy path, invalid JSON, empty strategies, missing seeds, unknown strategy)
#
# Do-Not-Change
#   Banner policy-relevant; modifications via explicit task only.
# ============================================================
"""
from __future__ import annotations
from typing import List, Dict, Any, Sequence
import json

from app.research.strategy_batch import run_strategy_batch, MovingAverageCrossover, RandomFlip, Strategy

_STRATEGY_REGISTRY: Dict[str, Strategy] = {
    "ma_crossover": MovingAverageCrossover(),
    "random_flip": RandomFlip(),
}


def _synthetic_price_series(n: int = 120) -> List[float]:
    base = 100.0
    series: List[float] = []
    for i in range(n):
        series.append(base + i * 0.1 + ((i % 10) - 5) * 0.05)
    return series


def run_strategy_batch_ui(
    strategies_json: str,
    param_grid_json: str,
    seeds_csv: str,
    price_series: Sequence[float] | None = None,
) -> Dict[str, Any]:
    try:
        strategies_raw = json.loads(strategies_json) if strategies_json.strip() else []
    except Exception as e:
        return {"error": f"strategies_json parse error: {e}"}
    if not isinstance(strategies_raw, list) or not all(isinstance(s, str) for s in strategies_raw):
        return {"error": "strategies_json must be JSON list of strategy names"}
    if not strategies_raw:
        return {"error": "no strategies provided"}
    strategies: List[Strategy] = []
    for name in strategies_raw:
        strat = _STRATEGY_REGISTRY.get(name)
        if not strat:
            return {"error": f"unknown strategy: {name}"}
        strategies.append(strat)
    try:
        param_grid = json.loads(param_grid_json) if param_grid_json.strip() else {}
    except Exception as e:
        return {"error": f"param_grid_json parse error: {e}"}
    if not isinstance(param_grid, dict) or not all(isinstance(v, list) for v in param_grid.values()):
        return {"error": "param_grid_json must be JSON object mapping param->list"}
    try:
        seeds = [int(s.strip()) for s in seeds_csv.split(',') if s.strip()] if seeds_csv.strip() else []
    except Exception as e:
        return {"error": f"seeds parse error: {e}"}
    if not seeds:
        return {"error": "no seeds provided"}
    ps = list(price_series) if price_series is not None else _synthetic_price_series()
    try:
        results, summary = run_strategy_batch(strategies, ps, param_grid, seeds)
    except Exception as e:
        return {"error": f"execution error: {e}"}
    return {"summary": summary, "results": results}

__all__ = ["run_strategy_batch_ui"]
