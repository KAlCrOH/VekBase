"""
# ============================================================
# Context Banner — test_risk_metrics_extended | Category: test
# Purpose: Validate ES95/ES99 and rolling VaR(95) metrics behind VEK_RISK_METRICS flag.

# ============================================================
"""
import os
from datetime import datetime, UTC, timedelta
from app.analytics.metrics import aggregate_metrics
from app.core.trade_model import Trade


def _make_trades():
    # Create deterministic sequence of BUY/SELL producing varied returns
    base_ts = datetime(2025,1,1, tzinfo=UTC)
    trades = []
    prices = [100, 102, 98, 105, 90, 110, 95, 115, 80, 120]  # alternating ups/downs
    # Build BUY then immediate SELL with different prices to create distribution
    for i, p in enumerate(prices):
        buy_ts = base_ts + timedelta(minutes=i*2)
        sell_ts = buy_ts + timedelta(minutes=1)
        trades.append(Trade(trade_id=f"b{i}", ts=buy_ts, ticker="XYZ", action="BUY", shares=1, price=p, fees=0.0))
        # SELL at p * (1 + delta) where delta derived from pattern
        delta = ((i % 5) - 2) * 0.05  # sequence of negative to positive shifts
        sell_price = p * (1 + delta)
        trades.append(Trade(trade_id=f"s{i}", ts=sell_ts, ticker="XYZ", action="SELL", shares=1, price=sell_price, fees=0.0))
    return trades


def test_extended_risk_metrics_flag(monkeypatch):
    monkeypatch.setenv("VEK_RISK_METRICS", "1")
    metrics = aggregate_metrics(_make_trades())
    # Basic presence
    assert "es_95" in metrics and "es_99" in metrics
    assert metrics["es_95"] >= 0 and metrics["es_99"] >= 0
    assert "rolling_var95_series" in metrics
    series = metrics["rolling_var95_series"]
    assert isinstance(series, list)
    # Rolling series length matches number of returns processed (SELL count) as we append each incremental window
    sells = metrics["sells"]
    assert len(series) == sells  # one value per available prefix (>=1) after threshold logic


def test_extended_risk_metrics_flag_off(monkeypatch):
    monkeypatch.delenv("VEK_RISK_METRICS", raising=False)
    metrics = aggregate_metrics(_make_trades())
    assert "es_95" not in metrics
    assert "rolling_var95_series" not in metrics