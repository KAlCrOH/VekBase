from datetime import datetime, UTC, timedelta
from app.research.failure_pattern_miner import extract_loss_features, cluster_losses, summarize_loss_clusters
from app.core.trade_model import Trade


def _loss_trade_pair(tid_base, entry_price, exit_price, start_minute):
    # Build a BUY then SELL realizing loss if exit<entry
    ts_entry = datetime(2025,1,1,tzinfo=UTC) + timedelta(minutes=start_minute)
    ts_exit = ts_entry + timedelta(minutes=5)
    return [
        Trade(trade_id=f"{tid_base}_b", ts=ts_entry, ticker="SIM", action="BUY", shares=1, price=entry_price, fees=0.0),
        Trade(trade_id=f"{tid_base}_s", ts=ts_exit, ticker="SIM", action="SELL", shares=1, price=exit_price, fees=0.0),
    ]


def test_extract_and_cluster_losses_separation():
    trades = []
    # Cluster 1: small quick losses
    for i in range(10):
        trades.extend(_loss_trade_pair(f"c1_{i}", 100.0, 99.5, i*10))
    # Cluster 2: larger losses
    for i in range(8):
        trades.extend(_loss_trade_pair(f"c2_{i}", 120.0, 114.0, 200 + i*15))
    features = extract_loss_features(trades)
    clusters = cluster_losses(features, k_max=4)
    assert len(clusters) >= 2
    # Largest avg_abs_loss cluster should correspond to bigger losses (~6 per trade vs 0.5)
    largest = clusters[0]
    assert largest["avg_abs_loss"] > 5.0
    smaller = clusters[-1]
    assert smaller["avg_abs_loss"] < largest["avg_abs_loss"]
    summary = summarize_loss_clusters(trades, clusters)
    assert summary["avoidable_loss_estimate"] > 0


def test_no_losses_edge():
    # All profitable trades
    trades = []
    for i in range(5):
        ts = datetime(2025,1,1,tzinfo=UTC) + timedelta(minutes=i*3)
        trades.append(Trade(trade_id=f"p{i}b", ts=ts, ticker="SIM", action="BUY", shares=1, price=100.0, fees=0.0))
        trades.append(Trade(trade_id=f"p{i}s", ts=ts + timedelta(minutes=2), ticker="SIM", action="SELL", shares=1, price=101.0, fees=0.0))
    features = extract_loss_features(trades)
    assert features == []
    clusters = cluster_losses(features, k_max=5)
    assert clusters == []
    summary = summarize_loss_clusters(trades, clusters)
    assert summary == {"loss_clusters": [], "avoidable_loss_estimate": 0.0}


def test_single_loss_edge():
    trades = _loss_trade_pair("solo", 100.0, 95.0, 0)
    features = extract_loss_features(trades)
    assert len(features) == 1
    clusters = cluster_losses(features, k_max=5)
    assert len(clusters) == 1
    summary = summarize_loss_clusters(trades, clusters)
    assert summary["avoidable_loss_estimate"] > 0


def test_determinism():
    trades = []
    for i in range(6):
        trades.extend(_loss_trade_pair(f"d{i}", 100.0 + i, 99.0 + i, i*7))
    f1 = extract_loss_features(trades)
    f2 = extract_loss_features(trades)
    assert f1 == f2
    c1 = cluster_losses(f1, k_max=3)
    c2 = cluster_losses(f2, k_max=3)
    assert c1 == c2
