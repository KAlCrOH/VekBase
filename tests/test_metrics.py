"""
# ============================================================
# Context Banner — test_metrics | Category: test
# Purpose: Prüft aggregierte Kennzahlen (realized/unrealized PnL, Drawdown, Holding-Dauer)

# Contracts
#   Inputs: synthetische Trades (Repo) + optional Mark Prices
#   Outputs: Assertions auf berechnete Felder
#   Side-Effects: none
#   Determinism: deterministic

# Invariants
#   - Unrealized Berechnung konsistent mit Modell (Remaining Lots)

# Dependencies
#   Internal: analytics.metrics, core.trade_model, core.trade_repo
#   External: stdlib (datetime)

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from app.analytics.metrics import aggregate_metrics
from datetime import datetime
from app.core.trade_model import validate_trade_dict
from app.core.trade_repo import TradeRepository


def build_repo():
    repo = TradeRepository()
    trades = [
        {"trade_id": "b1", "ts": "2024-01-01T09:00:00", "ticker": "ABC", "action": "BUY", "shares": 10, "price": 10, "fees": 0},
        {"trade_id": "b2", "ts": "2024-01-02T09:00:00", "ticker": "ABC", "action": "BUY", "shares": 5, "price": 12, "fees": 0},
        {"trade_id": "s1", "ts": "2024-01-03T09:00:00", "ticker": "ABC", "action": "SELL", "shares": 8, "price": 15, "fees": 1},
    ]
    for r in trades:
        repo.add_trade(validate_trade_dict(r))
    return repo


def test_aggregate_metrics():
    repo = build_repo()
    metrics = aggregate_metrics(repo.all())
    assert metrics["trades_total"] == 3
    assert metrics["sells"] == 1
    assert metrics["total_realized_pnl"] > 0
    assert "max_drawdown_realized" in metrics
    assert "cagr" in metrics


def test_unrealized_and_duration_metrics():
    # Build custom trades sequence with partial close and remaining open
    trades = [
        {"trade_id": "b1", "ts": "2024-01-01T10:00:00", "ticker": "XYZ", "action": "BUY", "shares": 5, "price": 10, "fees": 0},
        {"trade_id": "s1", "ts": "2024-01-01T11:00:00", "ticker": "XYZ", "action": "SELL", "shares": 2, "price": 12, "fees": 0},
        {"trade_id": "b2", "ts": "2024-01-01T12:00:00", "ticker": "XYZ", "action": "BUY", "shares": 1, "price": 11, "fees": 0},
    ]
    repo = TradeRepository()
    for t in trades:
        repo.add_trade(validate_trade_dict(t))
    mark_prices = {"XYZ": 13}
    metrics = aggregate_metrics(repo.all(), mark_prices=mark_prices, now=datetime(2024,1,1,13,0,0))
    # Realized pnl: (2 * (12-10)) = 4
    assert abs(metrics["total_realized_pnl"] - 4) < 1e-9
    # Unrealized: remaining lots 3@10 + 1@11 mark 13 -> 3*(3) + 1*(2) = 11
    assert abs(metrics["unrealized_pnl"] - 11) < 1e-9
    assert metrics["open_position_shares"] == 4
    assert metrics["avg_holding_duration_sec"] > 0
