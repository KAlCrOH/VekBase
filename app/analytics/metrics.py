# ============================================================
# Context Banner — metrics | Category: analytics
# Purpose: Berechnung von realisierten & ausgewählten unrealisierten Kennzahlen (PnL, Win-Rate, Profit-Factor, Drawdown, Holding-Dauer, Equity Curve)

# Contracts
#   Inputs: List[Trade]; optional mark_prices: Dict[ticker->price]; optional now: datetime
#   Outputs: Dict[str, float|str] (aggregate_metrics), List[(ts, equity)] (realized_equity_curve), List[TradePNL] via compute_realized_pnl
#   Side-Effects: File I/O=none; Network=none
#   Determinism: deterministic (sort by ts)

# Invariants
#   - Keine Hidden I/O, reine Berechnungen
#   - FIFO Matching für Realized PnL
#   - Mark-to-Market nur wenn mark_prices gesetzt
#   - Öffentliche Signaturen stabil (aggregate_metrics, realized_equity_curve, compute_realized_pnl)

# Dependencies
#   Internal: core.trade_model.Trade
#   External: stdlib (dataclasses, datetime, typing)

# Tests
#   tests/test_metrics.py (realized/unrealized + duration)
#   tests/test_equity_curve.py (Equity Curve)

# Do-Not-Change
#   Banner policy-relevant; Änderungen nur mit Task „Header aktualisieren“.
# ============================================================
from __future__ import annotations
from typing import List, Dict, Tuple
from datetime import datetime
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

def aggregate_metrics(trades: List[Trade], mark_prices: Dict[str, float] | None = None, now: datetime | None = None) -> Dict[str, float]:
    """Aggregate realized metrics plus optional unrealized and holding duration.
    mark_prices: current price per ticker for unrealized estimation. If omitted unrealized=0.
    now: timestamp used for marking duration of open positions (default = max trade ts).
    """
    pnl_entries, total_realized = compute_realized_pnl(trades)
    sells = [p for p in pnl_entries]
    wins = [p for p in sells if p.realized_pnl > 0]
    losses = [p for p in sells if p.realized_pnl <= 0]
    avg_trade = (sum(p.realized_pnl for p in sells) / len(sells)) if sells else 0.0
    total_fees = sum(p.fees for p in sells)
    cum = _cumulative([p.realized_pnl for p in sells])
    max_dd = _max_drawdown(cum)

    # Build inventory for unrealized + holding durations
    inv: Dict[str, List[Tuple[float, float, datetime]]] = {}  # ticker -> list of (shares_remaining, price, ts_open)
    closed_durations: List[float] = []  # seconds
    # replay trades
    for t in sorted(trades, key=lambda x: x.ts):
        if t.action == "BUY":
            inv.setdefault(t.ticker, []).append((t.shares, t.price, t.ts))
        else:  # SELL
            remaining = t.shares
            lots = inv.get(t.ticker, [])
            i = 0
            while remaining > 1e-12 and i < len(lots):
                lot_sh, lot_price, lot_ts = lots[i]
                take = min(lot_sh, remaining)
                lot_sh -= take
                remaining -= take
                # duration for portion closed
                closed_durations.append((t.ts - lot_ts).total_seconds())
                if lot_sh <= 1e-12:
                    lots.pop(i)
                else:
                    lots[i] = (lot_sh, lot_price, lot_ts)
                    i += 1

    # Unrealized mark-to-market
    unrealized = 0.0
    if mark_prices:
        for ticker, lots in inv.items():
            mp = mark_prices.get(ticker)
            if mp is None:
                continue
            for lot_sh, lot_price, _lot_ts in lots:
                unrealized += (mp - lot_price) * lot_sh

    avg_holding_duration = (sum(closed_durations) / len(closed_durations)) if closed_durations else 0.0
    now_ts = now or (max((t.ts for t in trades), default=datetime.utcnow()))
    open_positions = sum(lot_sh for lots in inv.values() for lot_sh, _, _ in lots)
    return {
        "trades_total": len(trades),
        "sells": len(sells),
        "win_rate": (len(wins) / len(sells)) if sells else 0.0,
        "avg_trade_pnl": avg_trade,
        "total_realized_pnl": total_realized,
        "total_fees": total_fees,
        "profit_factor": (sum(p.realized_pnl for p in wins) / abs(sum(p.realized_pnl for p in losses)) if losses else float('inf')) if sells else 0.0,
        "max_drawdown_realized": max_dd,
        "unrealized_pnl": unrealized,
        "avg_holding_duration_sec": avg_holding_duration,
        "open_position_shares": open_positions,
        "timestamp_now": now_ts.isoformat(),
    }

def realized_equity_curve(trades: List[Trade], start_equity: float = 0.0) -> List[Tuple]:
    """Return list of (timestamp, cumulative_realized_equity) using realized PnL only.
    Useful for charting in UI Dev console. Start equity can shift baseline.
    """
    pnl_entries, _ = compute_realized_pnl(trades)
    curve: List[Tuple] = []
    acc = start_equity
    for entry in pnl_entries:
        acc += entry.realized_pnl
        curve.append((entry.trade.ts, acc))
    return curve
