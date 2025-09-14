from datetime import datetime, UTC, timedelta
from app.research.regime_detection import compute_regime_labels, summarize_regime_returns
from app.core.trade_model import Trade


def _make_trades_from_prices(prices):
    # Simple buy then later sell pairs to generate realized increments roughly following price path
    trades = []
    trade_id = 0
    position = False
    for i, p in enumerate(prices):
        ts = datetime(2025,1,1,tzinfo=UTC) + timedelta(minutes=i)
        # enter on even indices, exit on odd, to alternate realized pnl segments
        if not position:
            trades.append(Trade(trade_id=f"t{trade_id}", ts=ts, ticker="SIM", action="BUY", shares=1, price=p, fees=0.0))
            position = True
        else:
            trades.append(Trade(trade_id=f"t{trade_id}", ts=ts, ticker="SIM", action="SELL", shares=1, price=p, fees=0.0))
            position = False
        trade_id += 1
    # close if open
    if position:
        ts = datetime(2025,1,1,tzinfo=UTC) + timedelta(minutes=len(prices))
        trades.append(Trade(trade_id=f"t{trade_id}", ts=ts, ticker="SIM", action="SELL", shares=1, price=prices[-1], fees=0.0))
    return trades


def test_regime_labels_basic_structure():
    prices = [100 + i*0.5 for i in range(120)]  # steady uptrend
    labels = compute_regime_labels(prices, window_vol=10, window_trend=10)
    assert len(labels) == len(prices)
    sample = labels[-1]
    assert {"idx", "price", "vol", "vol_bucket", "trend_slope", "trend_bucket"}.issubset(sample.keys())
    # With steady uptrend expect majority trend_bucket 'up' (after warmup)
    ups = sum(1 for l in labels if l["trend_bucket"] == "up")
    assert ups > len(prices) * 0.4  # loose check


def test_regime_vol_buckets_distribution():
    # Construct phases: low vol (flat), high vol (alternating), medium vol (mild trend)
    phase1 = [100 + 0.01*i for i in range(60)]  # low vol
    phase2 = [106 + ((-1)**i) * 0.8 for i in range(60)]  # high oscillation
    prices = phase1 + phase2
    labels = compute_regime_labels(prices, window_vol=15, window_trend=15)
    high_count = sum(1 for l in labels if l["vol_bucket"] == "high")
    low_count = sum(1 for l in labels if l["vol_bucket"] == "low")
    # Expect both some high and low classifications after warmup
    assert high_count > 5
    assert low_count > 5


def test_summarize_regime_returns_mapping():
    prices = [100 + (i*0.2) for i in range(40)]
    labels = compute_regime_labels(prices, window_vol=5, window_trend=5)
    trades = _make_trades_from_prices(prices)
    summary = summarize_regime_returns(trades, labels)
    assert "regimes" in summary and "global" in summary
    total_from_buckets = sum(r["total_pnl"] for r in summary["regimes"])  # may not match exactly due to mapping but should be close
    # Realized pnl approximates final equity (allow small drift if mapping coarse)
    assert abs(total_from_buckets - summary["global"]["total_pnl"]) < abs(summary["global"]["total_pnl"]) * 0.25 + 1e-6


def test_empty_inputs():
    assert compute_regime_labels([]) == []
    summary = summarize_regime_returns([], [])
    assert summary == {"regimes": [], "global": {"total_pnl": 0.0, "points": 0}}
