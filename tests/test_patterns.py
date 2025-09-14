"""
# ============================================================
# Context Banner — test_patterns | Category: test
# Purpose: Tests für Pattern Analytics Stubs (Histogram + Scatter)

# Contracts
#   Inputs: synthetische Trades
#   Outputs: Assertions auf Längen und Wertebereiche
#   Side-Effects: none
#   Determinism: deterministic

# Invariants
#   - Histogram Buckets nicht leer bei SELL
#   - Scatter Punkte Anzahl entspricht Anzahl gematchter Sell-Portionen

# Dependencies
#   Internal: analytics.patterns, core.trade_model, core.trade_repo
#   External: stdlib

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from app.analytics.patterns import holding_duration_histogram, entry_return_scatter
from app.core.trade_model import validate_trade_dict
from app.core.trade_repo import TradeRepository


def build_repo():
    repo = TradeRepository()
    rows = [
        {"trade_id": "b1", "ts": "2024-01-01T09:00:00", "ticker": "PAT", "action": "BUY", "shares": 5, "price": 10, "fees": 0},
        {"trade_id": "b2", "ts": "2024-01-01T10:00:00", "ticker": "PAT", "action": "BUY", "shares": 5, "price": 11, "fees": 0},
        {"trade_id": "s1", "ts": "2024-01-01T12:00:00", "ticker": "PAT", "action": "SELL", "shares": 6, "price": 12, "fees": 0},
    ]
    for r in rows:
        repo.add_trade(validate_trade_dict(r))
    return repo


def test_holding_duration_histogram():
    repo = build_repo()
    hist_res = holding_duration_histogram(repo.all(), bucket_minutes=30, max_buckets=5)
    # Accept dict (new) or list (legacy)
    if isinstance(hist_res, dict):
        buckets = hist_res['buckets']
        assert len(buckets) == 5
        assert sum(buckets) > 0
        assert 'p50' in hist_res and 'p90' in hist_res
    else:
        assert len(hist_res) == 5
        assert sum(hist_res) > 0  # at least one closed portion counted


def test_entry_return_scatter():
    repo = build_repo()
    pts = entry_return_scatter(repo.all())
    assert len(pts) > 0
    # returns should be finite numbers
    for price, ret in pts:
        assert price > 0
        assert -1 < ret < 10  # sanity bound


def test_empty_trades_patterns():
    # Empty repository should yield zeroed histogram and empty scatter
    from app.core.trade_repo import TradeRepository
    empty_repo = TradeRepository()
    hist_res = holding_duration_histogram(empty_repo.all(), bucket_minutes=15, max_buckets=4)
    if isinstance(hist_res, dict):
        assert hist_res['buckets'] == [0,0,0,0]
        assert hist_res['count'] == 0
    else:
        assert hist_res == [0,0,0,0]
    pts = entry_return_scatter(empty_repo.all())
    assert pts == []


def test_invalid_bucket_size():
    repo = build_repo()
    try:
        holding_duration_histogram(repo.all(), bucket_minutes=0)
        assert False, "Expected ValueError for bucket_minutes=0"
    except ValueError:
        pass
