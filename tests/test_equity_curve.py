from app.analytics.metrics import realized_equity_curve, aggregate_metrics
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