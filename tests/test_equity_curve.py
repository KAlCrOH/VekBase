"""
# ============================================================
# Context Banner — test_equity_curve | Category: test
# Purpose: Verifiziert dass realized_equity_curve nach erstem SELL positiven Wert liefert

# Contracts
#   Inputs: Trades (2x BUY, 1x SELL) -> Repo
#   Outputs: Assertions auf Länge und positiver Equity Punkt
#   Side-Effects: none
#   Determinism: deterministic

# Invariants
#   - Nur SELL erzeugt Punkt in Kurve

# Dependencies
#   Internal: analytics.metrics, core.trade_model, core.trade_repo
#   External: stdlib

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from app.analytics.metrics import realized_equity_curve, aggregate_metrics, realized_equity_curve_with_unrealized, drawdown_curve
from app.core.trade_model import validate_trade_dict
from app.core.trade_repo import TradeRepository


def test_realized_equity_curve_progresses():
    repo = TradeRepository()
    rows = [
        {"trade_id": "b1", "ts": "2024-01-01T09:00:00", "ticker": "AAA", "action": "BUY", "shares": 5, "price": 10, "fees": 0},
        {"trade_id": "b2", "ts": "2024-01-02T09:00:00", "ticker": "AAA", "action": "BUY", "shares": 5, "price": 11, "fees": 0},
        {"trade_id": "s1", "ts": "2024-01-03T09:00:00", "ticker": "AAA", "action": "SELL", "shares": 5, "price": 12, "fees": 0},
    ]
    for r in rows:
        repo.add_trade(validate_trade_dict(r))
    curve = realized_equity_curve(repo.all())
    # Only one SELL -> one point in realized curve
    assert len(curve) == 1
    ts, val = curve[0]
    assert val > 0


def test_equity_curve_with_unrealized_append_point():
    repo = TradeRepository()
    rows = [
        {"trade_id": "b1", "ts": "2024-01-01T09:00:00", "ticker": "BBB", "action": "BUY", "shares": 5, "price": 10, "fees": 0},
        {"trade_id": "s1", "ts": "2024-01-02T09:00:00", "ticker": "BBB", "action": "SELL", "shares": 2, "price": 12, "fees": 0},
    ]
    for r in rows:
        repo.add_trade(validate_trade_dict(r))
    # After 1 partial sell, realized curve length 1; open position remains 3 shares.
    base = realized_equity_curve(repo.all())
    assert len(base) == 1
    curve_ext = realized_equity_curve_with_unrealized(repo.all(), mark_prices={"BBB": 13})
    # Should add an extra point (final unrealized) because open shares exist.
    assert len(curve_ext) == 2
    # Second point equity should be > first point
    assert curve_ext[1][1] > curve_ext[0][1]


def test_equity_curve_with_unrealized_no_mark_prices():
    repo = TradeRepository()
    rows = [
        {"trade_id": "b1", "ts": "2024-01-01T09:00:00", "ticker": "CCC", "action": "BUY", "shares": 4, "price": 5, "fees": 0},
        {"trade_id": "s1", "ts": "2024-01-01T10:00:00", "ticker": "CCC", "action": "SELL", "shares": 2, "price": 6, "fees": 0},
    ]
    for r in rows:
        repo.add_trade(validate_trade_dict(r))
    base = realized_equity_curve(repo.all())
    ext = realized_equity_curve_with_unrealized(repo.all())
    assert base == ext  # no mark prices so no extension


def test_drawdown_curve_basic():
    # Synthetic small curve with a drawdown
    from datetime import datetime
    curve = [
        (datetime(2024,1,1,9,0,0), 0.0),
        (datetime(2024,1,1,10,0,0), 10.0),  # peak
        (datetime(2024,1,1,11,0,0), 8.0),   # drawdown  -20%
        (datetime(2024,1,1,12,0,0), 12.0),  # new peak
    ]
    dd = drawdown_curve(curve)
    assert len(dd) == 4
    # Third point should have negative drawdown_pct ~ -0.2
    third = dd[2]
    assert third['drawdown_pct'] < 0
    # Peaks have 0 drawdown
    assert dd[1]['drawdown_pct'] == 0
    assert dd[3]['drawdown_pct'] == 0


def test_drawdown_curve_empty():
    assert drawdown_curve([]) == []