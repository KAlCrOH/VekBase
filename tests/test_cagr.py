"""
# ============================================================
# Context Banner — test_cagr | Category: test
# Purpose: Verifiziert CAGR Berechnung aus realized Equity Curve.

# Contracts
#   Inputs: synthetische Trades → metrics.aggregate_metrics
#   Outputs: Assertions auf cagr Feld
#   Side-Effects: none
#   Determinism: deterministic

# Invariants
#   - cagr=0.0 bei zu kurzer oder 0-Dauer Kurve

# Dependencies
#   Internal: analytics.metrics, core.trade_model, core.trade_repo
#   External: stdlib (datetime)

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from datetime import datetime, timedelta
from app.core.trade_repo import TradeRepository
from app.core.trade_model import validate_trade_dict
from app.analytics.metrics import aggregate_metrics, realized_equity_curve
from app.core.decision_card import make_decision_card


def _add(repo: TradeRepository, items):
    for r in items:
        repo.add_trade(validate_trade_dict(r))


def test_cagr_positive():
    repo = TradeRepository()
    # Simple growth: buy low sell high sequence
    _add(repo, [
        {"trade_id": "b1", "ts": "2024-01-01T00:00:00", "ticker": "AAA", "action": "BUY", "shares": 1, "price": 100},
        {"trade_id": "s1", "ts": "2024-07-01T00:00:00", "ticker": "AAA", "action": "SELL", "shares": 1, "price": 110},
    ])
    metrics = aggregate_metrics(repo.all())
    assert "cagr" in metrics
    # ~10% nominal in ~0.5 Jahre => annualisiert leicht höher als nominal > 0
    assert metrics["cagr"] > 0


def test_cagr_edge_short_series():
    repo = TradeRepository()
    _add(repo, [
        {"trade_id": "b1", "ts": "2024-01-01T00:00:00", "ticker": "BBB", "action": "BUY", "shares": 1, "price": 50},
    ])
    metrics = aggregate_metrics(repo.all())
    assert metrics["cagr"] == 0.0  # nur ein Punkt -> keine Dauer


def test_timezone_awareness_created_at_and_metrics():
    card = make_decision_card("tz1", author="tester", title="TZ Test")
    assert card.to_dict()["created_at"].endswith("+00:00")
    repo = TradeRepository()
    _add(repo, [
        {"trade_id": "b1", "ts": "2024-01-01T09:00:00", "ticker": "TZ", "action": "BUY", "shares": 1, "price": 10, "fees": 0},
    ])
    metrics = aggregate_metrics(repo.all())
    assert metrics["timestamp_now"].endswith("+00:00")
