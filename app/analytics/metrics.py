# ============================================================
# Context Banner — metrics | Category: analytics
# Purpose: Berechnung von REALIZED Kennzahlen + optionale unrealized Felder (nur wenn mark_prices gesetzt) (PnL, Win-Rate, Profit-Factor, realized Drawdown, Holding-Dauer, realized Equity Curve)

# Contracts
#   Inputs: List[Trade]; optional mark_prices: Dict[ticker->price]; optional now: datetime
#   Outputs: Dict[str, float|str] (aggregate_metrics), List[(ts, equity)] (realized_equity_curve), List[TradePNL] via compute_realized_pnl
#   Side-Effects: File I/O=none; Network=none
#   Determinism: deterministic (sort by ts)

# Invariants
#   - Keine Hidden I/O, reine Berechnungen
#   - FIFO Matching für Realized PnL
#   - Mark-to-Market nur wenn mark_prices gesetzt (sonst unrealized_pnl=0)
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
from datetime import datetime, UTC
from dataclasses import dataclass
from ..core.trade_model import Trade
from math import pow

@dataclass
class TradePNL:
    trade: Trade
    realized_pnl: float
    fees: float
    cost_basis: float  # Summe der ursprünglichen Kosten (für realisierten Anteil) – für CAGR Ableitung bei Einzel-Sell

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
            cost_basis = 0.0
            i = 0
            while remaining > 1e-12 and i < len(inv):
                lot_shares, lot_price = inv[i]
                take = min(lot_shares, remaining)
                realized += (t.price - lot_price) * take
                cost_basis += lot_price * take
                lot_shares -= take
                remaining -= take
                if lot_shares <= 1e-12:
                    inv.pop(i)
                else:
                    inv[i] = (lot_shares, lot_price)
                    i += 1
            total += realized - t.fees
            out.append(TradePNL(trade=t, realized_pnl=realized - t.fees, fees=t.fees, cost_basis=cost_basis))
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

def _cagr_from_curve(curve: List[Tuple[datetime, float]]) -> float:  # type: ignore[name-defined]
    """Compute CAGR basierend auf erster/letzter Equity und Zeitdelta in Jahren.
    Erwartet Liste (ts, equity); falls unzureichend Daten oder Zeitraum 0 -> 0.0.
    """
    if not curve or len(curve) < 2:
        return 0.0
    start_ts, start_eq = curve[0]
    end_ts, end_eq = curve[-1]
    if start_eq <= 0:
        return 0.0
    delta_days = (end_ts - start_ts).total_seconds() / 86400.0
    if delta_days <= 0:
        return 0.0
    years = delta_days / 365.0
    if years <= 0:
        return 0.0
    multiple = end_eq / start_eq
    if multiple <= 0:
        return 0.0
    try:
        return pow(multiple, 1/years) - 1
    except Exception:
        return 0.0

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
    now_ts = now or (max((t.ts for t in trades), default=datetime.now(UTC)))
    # Normalize to UTC aware if naive (assume naive timestamps are UTC-based input)
    if now_ts.tzinfo is None:
        now_ts = now_ts.replace(tzinfo=UTC)
    open_positions = sum(lot_sh for lots in inv.values() for lot_sh, _, _ in lots)
    result = {
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
    # CAGR nur wenn ausreichend realisierte Kurve existiert
    realized_curve = realized_equity_curve(trades)
    # Standardfall: >=2 Punkte -> klassischer CAGR über Equity Kurve (realized PnL kumulativ)
    if len(realized_curve) >= 2:
        result["cagr"] = _cagr_from_curve(realized_curve)
    elif len(realized_curve) == 1 and sells:
        # Spezialfall: Nur ein realisierter Punkt (ein SELL). Verwende Kostenbasis des SELL zur Bestimmung eines Startkapitals.
        single_ts, single_equity = realized_curve[0]
        # Finde zugehörigen SELL Eintrag (gleiche ts) – falls mehrere an dem Tag, nimm ersten Match
        sell_entry = next((p for p in sells if p.trade.ts == single_ts), None)
        if sell_entry and sell_entry.cost_basis > 0 and single_equity > 0:
            start_ts = min((t.ts for t in trades), default=single_ts)
            if single_ts > start_ts:
                delta_days = (single_ts - start_ts).total_seconds() / 86400.0
                if delta_days > 0:
                    years = delta_days / 365.0
                    if years > 0:
                        # multiple = (cost_basis + realized_pnl) / cost_basis
                        multiple = (sell_entry.cost_basis + sell_entry.realized_pnl) / sell_entry.cost_basis
                        if multiple > 0:
                            try:
                                result["cagr"] = pow(multiple, 1/years) - 1
                            except Exception:
                                result["cagr"] = 0.0
                        else:
                            result["cagr"] = 0.0
                    else:
                        result["cagr"] = 0.0
                else:
                    result["cagr"] = 0.0
            else:
                result["cagr"] = 0.0
        else:
            result["cagr"] = 0.0
    else:
        result["cagr"] = 0.0
    return result

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


def realized_equity_curve_with_unrealized(  # non-breaking new helper
    trades: List[Trade],
    mark_prices: Dict[str, float] | None = None,
    now: datetime | None = None,
    start_equity: float = 0.0,
) -> List[Tuple[datetime, float]]:
    """Return realized equity curve optionally extended by a final point including unrealized PnL.
    Behavior:
      - If no mark_prices provided or no open positions -> identical to realized_equity_curve.
      - If open positions AND mark_prices -> append (now_ts, realized_equity + unrealized_pnl).
    Deterministic given inputs.
    """
    base_curve = realized_equity_curve(trades, start_equity=start_equity)
    if not mark_prices:
        return base_curve
    # Reuse aggregation logic (single pass) for unrealized calculation
    metrics = aggregate_metrics(trades, mark_prices=mark_prices, now=now)
    unreal = metrics.get("unrealized_pnl", 0.0)
    if unreal == 0:
        return base_curve
    realized_val = base_curve[-1][1] if base_curve else 0.0
    ts_now = datetime.fromisoformat(metrics["timestamp_now"]) if "timestamp_now" in metrics else (now or datetime.now(UTC))
    extended = list(base_curve)
    extended.append((ts_now, realized_val + unreal))
    return extended


def drawdown_curve(equity_curve: List[Tuple[datetime, float]]) -> List[Dict[str, float | str]]:
    """Return drawdown series from an equity curve.
    Input: list of (ts, equity). Output: list of {'ts': ISO, 'equity': val, 'drawdown_pct': pct}.
    drawdown_pct <= 0 (0 at peaks). If equity <=0 or peak<=0 -> drawdown 0 to avoid division noise.
    Deterministic and pure.
    Edge cases: empty -> []. Single point -> dd=0.
    """
    if not equity_curve:
        return []
    peak = equity_curve[0][1]
    out: List[Dict[str, float | str]] = []
    for ts, val in equity_curve:
        if val > peak:
            peak = val
        if peak <= 0 or val <= 0:
            dd_pct = 0.0
        else:
            dd_pct = (val / peak) - 1.0  # negative or 0
        out.append({"ts": ts.isoformat(), "equity": val, "drawdown_pct": round(dd_pct, 6)})
    return out


def position_size_series(trades: List[Trade]) -> List[Dict[str, float | str]]:
    """Return time series of gross exposure measured as sum(shares*price) of open lots per timestamp.
    Simplistic: uses trade execution price as mark.
    Output: list of {'ts': ISO, 'gross_exposure': float} sorted by ts.
    """
    inv: Dict[str, List[Tuple[float, float]]] = {}  # ticker -> list(lot_shares, lot_price)
    series: List[Dict[str, float | str]] = []
    for t in sorted(trades, key=lambda x: x.ts):
        if t.action == "BUY":
            inv.setdefault(t.ticker, []).append((t.shares, t.price))
        else:  # SELL
            remaining = t.shares
            lots = inv.get(t.ticker, [])
            i = 0
            while remaining > 1e-12 and i < len(lots):
                lot_sh, lot_price = lots[i]
                take = min(lot_sh, remaining)
                lot_sh -= take
                remaining -= take
                if lot_sh <= 1e-12:
                    lots.pop(i)
                else:
                    lots[i] = (lot_sh, lot_price)
                    i += 1
        gross = 0.0
        for _ticker, lots in inv.items():
            for lot_sh, lot_price in lots:
                gross += lot_sh * lot_price
        series.append({"ts": t.ts.isoformat(), "gross_exposure": round(gross, 6)})
    return series


def unrealized_equity_timeline(
    trades: List[Trade],
    mark_prices: Dict[str, float],
    now: datetime | None = None,
) -> List[Tuple[datetime, float]]:
    """Return time series of unrealized equity value over time using provided mark_prices for open positions.
    Approach:
      - Replay trades chronologisch; nach jedem Trade aktuellen unrealized Wert (basierend auf mark_prices falls verfügbar) berechnen.
      - Falls ein Ticker keine mark_price hat -> dessen Lots ignorieren (konservativ).
      - Optional finaler Punkt (now) falls now > letzter Trade ts und offene Positionen existieren.
    Returns list[(ts, unrealized_equity)]. Empty if no trades or no mark prices.
    Deterministic & pure.
    Edge Cases:
      - Keine mark_prices -> []
      - Alle Positionen geschlossen -> evtl. Zwischenwerte vorhanden, final 0 falls keine offenen.
    """
    if not mark_prices:
        return []
    inv: Dict[str, List[Tuple[float, float]]] = {}  # ticker -> list(lot_shares, lot_price)
    timeline: List[Tuple[datetime, float]] = []
    sorted_trades = sorted(trades, key=lambda x: x.ts)
    for t in sorted_trades:
        if t.action == "BUY":
            inv.setdefault(t.ticker, []).append((t.shares, t.price))
        else:
            lots = inv.get(t.ticker, [])
            remaining = t.shares
            i = 0
            while remaining > 1e-12 and i < len(lots):
                lot_sh, lot_price = lots[i]
                take = min(lot_sh, remaining)
                lot_sh -= take
                remaining -= take
                if lot_sh <= 1e-12:
                    lots.pop(i)
                else:
                    lots[i] = (lot_sh, lot_price)
                    i += 1
        # compute unrealized at this timestamp
        unreal = 0.0
        for ticker, lots in inv.items():
            mp = mark_prices.get(ticker)
            if mp is None:
                continue
            for lot_sh, lot_price in lots:
                unreal += (mp - lot_price) * lot_sh
        timeline.append((t.ts, unreal))
    if not timeline:
        return []
    if now and timeline:
        last_ts = timeline[-1][0]
        if now > last_ts:
            # recompute unrealized at now (inventory unchanged)
            unreal = 0.0
            for ticker, lots in inv.items():
                mp = mark_prices.get(ticker)
                if mp is None:
                    continue
                for lot_sh, lot_price in lots:
                    unreal += (mp - lot_price) * lot_sh
            timeline.append((now, unreal))
    return timeline


def unrealized_equity_timeline_by_ticker(
    trades: List[Trade],
    mark_prices: Dict[str, float],
    now: datetime | None = None,
) -> Dict[str, List[Tuple[datetime, float]]]:
    """Return per-ticker unrealized timelines.
    Returns dict[ticker] -> list[(ts, unrealized_value_for_that_ticker_at_ts)].
    Only includes tickers present in trades and with at least one lot. Marks missing -> ticker excluded.
    Adds optional final now point if provided and > last trade ts.
    Deterministic & pure.
    """
    if not mark_prices:
        return {}
    # Collect trades per ticker for deterministic replay per ticker
    by_ticker: Dict[str, List[Trade]] = {}
    for t in trades:
        by_ticker.setdefault(t.ticker, []).append(t)
    out: Dict[str, List[Tuple[datetime, float]]] = {}
    for ticker, tlist in by_ticker.items():
        mark = mark_prices.get(ticker)
        if mark is None:
            continue
        lots: List[Tuple[float, float]] = []
        series: List[Tuple[datetime, float]] = []
        for tr in sorted(tlist, key=lambda x: x.ts):
            if tr.action == "BUY":
                lots.append((tr.shares, tr.price))
            else:
                remaining = tr.shares
                i = 0
                while remaining > 1e-12 and i < len(lots):
                    lot_sh, lot_price = lots[i]
                    take = min(lot_sh, remaining)
                    lot_sh -= take
                    remaining -= take
                    if lot_sh <= 1e-12:
                        lots.pop(i)
                    else:
                        lots[i] = (lot_sh, lot_price)
                        i += 1
            unreal = 0.0
            for lot_sh, lot_price in lots:
                unreal += (mark - lot_price) * lot_sh
            series.append((tr.ts, unreal))
        if not series:
            continue
        if now and series and now > series[-1][0]:
            unreal = 0.0
            for lot_sh, lot_price in lots:
                unreal += (mark - lot_price) * lot_sh
            series.append((now, unreal))
        out[ticker] = series
    return out


def rolling_volatility(equity_curve: List[Tuple[datetime, float]], window: int = 5) -> List[Dict[str, float | str]]:
    """Compute rolling volatility (std dev of incremental returns) over realized equity curve.
    Returns list of {'ts': ISO, 'vol': float}. For first (window-1) points vol=None.
    Incremental returns defined as diff / prev_equity (skip if prev_equity==0).
    Deterministic & pure.
    """
    if window <= 1:
        raise ValueError("window must be >1")
    if not equity_curve:
        return []
    rets: List[float] = []
    out: List[Dict[str, float | str]] = []
    prev_val = equity_curve[0][1]
    out.append({"ts": equity_curve[0][0].isoformat(), "vol": None})
    for ts, val in equity_curve[1:]:
        if prev_val != 0:
            ret = (val - prev_val) / abs(prev_val)
        else:
            ret = 0.0
        rets.append(ret)
        prev_val = val
        if len(rets) >= window:
            window_slice = rets[-window:]
            mean = sum(window_slice)/len(window_slice)
            var = sum((x-mean)**2 for x in window_slice)/len(window_slice)
            vol = var ** 0.5
            out.append({"ts": ts.isoformat(), "vol": round(vol, 6)})
        else:
            out.append({"ts": ts.isoformat(), "vol": None})
    return out
