# ============================================================
# Context Banner — simple_walk | Category: sim
# Purpose: Deterministische Walk-Forward Mini-Simulation mit Momentum-Regel + Persistenz (meta.json, equity.csv)
# Gap: Erweiterte Parameter (TP/SL/Kosten) laut UI Spec / Roadmap noch offen (Backlog Hinweis)

# Contracts
#   Inputs: prices: List[(datetime, price)], rule(history)->'BUY'|'SELL'|'HOLD', seed:int, optional params (initial_cash, trade_size)
#   Outputs: SimResult (equity_curve, final_cash, meta{'seed','hash'}) / Persistenz Ordner via run_and_persist
#   Side-Effects: File I/O=write: data/results/<timestamp>_<hash>/{meta.json,equity.csv} (nur run_and_persist); Network=none
#   Determinism: seeded (hash basiert auf Parametern)

# Invariants
#   - Keine Look-Ahead Nutzung: Regel sieht nur Historie bis i
#   - Kein Hidden I/O in run_sim (Persistenz ausschließlich in run_and_persist)
#   - Seed + Parameter bestimmen Hash (Reproduzierbarkeit)

# Dependencies
#   Internal: none (kann von ui.console genutzt werden)
#   External: stdlib (hashlib, random, datetime, pathlib, json, csv, dataclasses)

# Tests
#   tests/test_simulation.py (Determinismus)
#   tests/test_sim_persist.py (Persistenz-Struktur)

# Do-Not-Change
#   Banner policy-relevant; Änderungen nur via Task „Header aktualisieren“.
# ============================================================
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Callable, Dict, Any, Optional
import hashlib
import random
from datetime import datetime, UTC
from pathlib import Path
import json
import csv

@dataclass
class SimResult:
    equity_curve: List[Tuple[datetime, float]]
    final_cash: float
    meta: Dict[str, Any]
    folder: Path | None = field(default=None)  # optional Persistenzpfad (nur gesetzt von run_and_persist)

def run_sim(
    prices: List[Tuple[datetime, float]],
    rule: Callable[[List[Tuple[datetime, float]]], str],
    seed: int,
    initial_cash: float = 10_000.0,
    trade_size: float = 0.1,
    take_profit_pct: Optional[float] = None,
    stop_loss_pct: Optional[float] = None,
    fee_rate_pct: float = 0.0,
) -> SimResult:
    """Run simple simulation with optional TP/SL and fee model.

    Parameters
    ----------
    prices : list[(datetime, float)]
        Time ordered price series.
    rule : callable(history)->str
        Returns one of 'BUY','SELL','HOLD'. Only past history (inclusive) supplied.
    seed : int
        Random seed (reserved for future stochastic extensions; ensures hash stability).
    initial_cash : float, default 10_000.0
    trade_size : float, default 0.1
        Fraction of *current available cash* allocated on each BUY signal.
    take_profit_pct : float | None
        If set and unrealized return >= this percent (e.g. 0.05 = +5%), position is force-closed at current price.
    stop_loss_pct : float | None
        If set and unrealized return <= -this percent, position is force-closed at current price.
    fee_rate_pct : float, default 0.0
        Proportional fee applied on notional for each BUY and SELL (e.g. 0.001 = 0.1%).

    Notes
    -----
    - Backward compatible: leaving TP/SL None & fee 0 reproduces legacy behavior.
    - Hash incorporates new parameters to preserve determinism guarantees.
    - Cost basis tracked for average entry to compute unrealized PnL.
    """
    rnd = random.Random(seed)
    cash = initial_cash
    shares = 0.0
    cost_basis = 0.0  # total cost invested in current open position (excluding fees on sell)
    curve: List[Tuple[datetime, float]] = []
    for i in range(len(prices)):
        history = prices[: i + 1]
        ts, price = history[-1]
        decision = rule(history)
        if decision == 'BUY' and cash > 0:
            alloc = cash * trade_size
            if alloc > 0 and price > 0:
                fee_buy = alloc * fee_rate_pct if fee_rate_pct > 0 else 0.0
                buy_shares = alloc / price
                shares += buy_shares
                cost_basis += alloc  # track capital deployed (without fee)
                cash -= (alloc + fee_buy)
        elif decision == 'SELL' and shares > 0:
            proceeds = shares * price
            fee_sell = proceeds * fee_rate_pct if fee_rate_pct > 0 else 0.0
            cash += proceeds - fee_sell
            shares = 0.0
            cost_basis = 0.0

        # Threshold-based forced exits (override rule) AFTER applying rule decision.
        if shares > 0 and cost_basis > 0:
            unrealized_ret = (shares * price - cost_basis) / cost_basis if cost_basis > 0 else 0.0
            tp_hit = take_profit_pct is not None and unrealized_ret >= take_profit_pct
            sl_hit = stop_loss_pct is not None and unrealized_ret <= -stop_loss_pct
            if tp_hit or sl_hit:
                proceeds = shares * price
                fee_sell = proceeds * fee_rate_pct if fee_rate_pct > 0 else 0.0
                cash += proceeds - fee_sell
                shares = 0.0
                cost_basis = 0.0
        # HOLD does nothing
        equity = cash + shares * price
        curve.append((ts, equity))
    hash_input = f"{seed}|{initial_cash}|{trade_size}|{len(prices)}|{take_profit_pct}|{stop_loss_pct}|{fee_rate_pct}".encode()
    sim_hash = hashlib.sha256(hash_input).hexdigest()[:12]
    return SimResult(equity_curve=curve, final_cash=equity, meta={"seed": seed, "hash": sim_hash})

# Example rule factories

def momentum_rule(window: int = 3) -> Callable[[List[Tuple[datetime, float]]], str]:
    def rule(hist: List[Tuple[datetime, float]]):
        if len(hist) < window + 1:
            return 'HOLD'
        recent = [p for _, p in hist[-window:]]
        prev = hist[-window-1][1]
        if all(p > prev for p in recent):
            return 'BUY'
        if all(p < prev for p in recent):
            return 'SELL'
        return 'HOLD'
    return rule

def run_and_persist(prices: List[Tuple[datetime, float]], rule: Callable[[List[Tuple[datetime, float]]], str], seed: int, results_dir: Path, **kwargs) -> SimResult:
    """Run simulation and persist under data/results/<timestamp>_<hash>/ (creates folder).
    Saves: meta.json, equity.csv. Returns SimResult.
    """
    results_dir.mkdir(parents=True, exist_ok=True)
    res = run_sim(prices, rule, seed=seed, **kwargs)
    ts_label = datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')
    folder = results_dir / f"{ts_label}_{res.meta['hash']}"
    folder.mkdir(parents=True, exist_ok=True)
    # meta
    meta_path = folder / 'meta.json'
    meta_content = {"seed": res.meta['seed'], "hash": res.meta['hash'], "final_cash": res.final_cash, "params": {k: v for k, v in kwargs.items()}}
    meta_path.write_text(json.dumps(meta_content, indent=2), encoding='utf-8')
    # equity
    eq_path = folder / 'equity.csv'
    with eq_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['ts', 'equity'])
        for ts, val in res.equity_curve:
            w.writerow([ts.isoformat(), f"{val:.6f}"])
    res.folder = folder
    return res
