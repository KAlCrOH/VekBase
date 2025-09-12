"""Deterministic walk-forward simulation.
Takes initial cash, list of trades (planned) decisions produced via a trivial rule.
No look-ahead: only past prices considered.
Prices passed explicitly (list of (ts, price)).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Callable, Dict, Any
import hashlib
import random
from datetime import datetime
from pathlib import Path
import json
import csv

@dataclass
class SimResult:
    equity_curve: List[Tuple[datetime, float]]
    final_cash: float
    meta: Dict[str, Any]

def run_sim(prices: List[Tuple[datetime, float]], rule: Callable[[List[Tuple[datetime, float]]], str], seed: int, initial_cash: float = 10_000.0, trade_size: float = 0.1) -> SimResult:
    """Run simple simulation.
    rule: function that given past price history returns one of: 'BUY','SELL','HOLD'
    trade_size: fraction of current cash to deploy when buying.
    Determinism via explicit seed.
    """
    rnd = random.Random(seed)
    cash = initial_cash
    shares = 0.0
    curve: List[Tuple[datetime, float]] = []
    for i in range(len(prices)):
        history = prices[: i + 1]
        ts, price = history[-1]
        decision = rule(history)
        if decision == 'BUY' and cash > 0:
            alloc = cash * trade_size
            buy_shares = alloc / price if price > 0 else 0
            shares += buy_shares
            cash -= alloc
        elif decision == 'SELL' and shares > 0:
            # sell all
            cash += shares * price
            shares = 0.0
        # HOLD does nothing
        equity = cash + shares * price
        curve.append((ts, equity))
    hash_input = f"{seed}|{initial_cash}|{trade_size}|{len(prices)}".encode()
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
    ts_label = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
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
    return res
