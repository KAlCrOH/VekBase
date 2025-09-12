from app.analytics.metrics import aggregate_metrics
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
