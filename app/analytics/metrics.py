"""Basic portfolio/trade metrics.
All functions pure: input = list[Trade], output = dict/values.
No hidden I/O. Extend later for DuckDB if needed.
"""
from __future__ import annotations
from typing import List, Dict, Tuple
from dataclasses import dataclass
from ..core.trade_model import Trade

@dataclass
class TradePNL:
    trade: Trade
    realized_pnl: float
    fees: float

def compute_realized_pnl(trades: List[Trade]) -> Tuple[List[TradePNL], float]:
    """FIFO matching within each ticker. Returns list of per-trade realized pnl (only for SELL trades) and total pnl.
    BUY adds to inventory; SELL matches earliest buys.
    """
    by_ticker: Dict[str, List[Tuple[float, float]]] = {}  # ticker -> list of (shares_remaining, price)
    out: List[TradePNL] = []
    total = 0.0
    for t in sorted(trades, key=lambda x: x.ts):
        if t.action == "BUY":
            by_ticker.setdefault(t.ticker, []).append((t.shares, t.price))
        else:  # SELL
            inv = by_ticker.get(t.ticker, [])
            remaining = t.shares
            realized = 0.0
            i = 0
            while remaining > 1e-12 and i < len(inv):
                lot_shares, lot_price = inv[i]
                take = min(lot_shares, remaining)
                realized += (t.price - lot_price) * take
                lot_shares -= take
                remaining -= take
                if lot_shares <= 1e-12:
                    inv.pop(i)
                else:
                    inv[i] = (lot_shares, lot_price)
                    i += 1
            total += realized - t.fees
            out.append(TradePNL(trade=t, realized_pnl=realized - t.fees, fees=t.fees))
    return out, total

def _cumulative(values: List[float]) -> List[float]:
    out: List[float] = []
    acc = 0.0
    for v in values:
        acc += v
        out.append(acc)
    return out

def _max_drawdown(series: List[float]) -> float:
    if not series:
        return 0.0
    peak = series[0]
    max_dd = 0.0
    for v in series:
        if v > peak:
            peak = v
        dd = v - peak
        if dd < max_dd:
            max_dd = dd
    return abs(max_dd)

def aggregate_metrics(trades: List[Trade]) -> Dict[str, float]:
    """Aggregate realized metrics (no unrealized yet)."""
    pnl_entries, total_realized = compute_realized_pnl(trades)
    sells = [p for p in pnl_entries]
    wins = [p for p in sells if p.realized_pnl > 0]
    losses = [p for p in sells if p.realized_pnl <= 0]
    avg_trade = (sum(p.realized_pnl for p in sells) / len(sells)) if sells else 0.0
    total_fees = sum(p.fees for p in sells)
    cum = _cumulative([p.realized_pnl for p in sells])
    max_dd = _max_drawdown(cum)
    return {
        "trades_total": len(trades),
        "sells": len(sells),
        "win_rate": (len(wins) / len(sells)) if sells else 0.0,
        "avg_trade_pnl": avg_trade,
        "total_realized_pnl": total_realized,
        "total_fees": total_fees,
        "profit_factor": (sum(p.realized_pnl for p in wins) / abs(sum(p.realized_pnl for p in losses)) if losses else float('inf')) if sells else 0.0,
        "max_drawdown_realized": max_dd,
    }
