"""
# ============================================================
# Context Banner — test_analytics_ext | Category: test
# Purpose: Tests für neue Analytics Funktionen (holding_duration_histogram stats, return_distribution, position_size_series)
# ============================================================
"""
from app.analytics.patterns import holding_duration_histogram, return_distribution
from app.analytics.metrics import position_size_series
from app.core.trade_model import validate_trade_dict
from app.core.trade_repo import TradeRepository


def _build_repo():
    repo = TradeRepository()
    rows = [
        {"trade_id":"b1","ts":"2024-01-01T09:00:00","ticker":"AAA","action":"BUY","shares":5,"price":10,"fees":0},
        {"trade_id":"b2","ts":"2024-01-01T10:00:00","ticker":"AAA","action":"BUY","shares":5,"price":11,"fees":0},
        {"trade_id":"s1","ts":"2024-01-01T11:30:00","ticker":"AAA","action":"SELL","shares":6,"price":12,"fees":0},
        {"trade_id":"s2","ts":"2024-01-02T09:00:00","ticker":"AAA","action":"SELL","shares":4,"price":13,"fees":0},
    ]
    for r in rows:
        repo.add_trade(validate_trade_dict(r))
    return repo


def test_holding_duration_histogram_stats():
    repo = _build_repo()
    res = holding_duration_histogram(repo.all(), bucket_minutes=60, max_buckets=5)
    assert isinstance(res, dict)
    assert 'buckets' in res and len(res['buckets']) == 5
    assert 'p50' in res and 'p90' in res
    assert res['count'] > 0
    assert 'p95' in res and 'overflow_count' in res


def test_return_distribution_basic():
    repo = _build_repo()
    dist = return_distribution(repo.all(), bucket_size=0.05)
    assert isinstance(dist, dict)
    assert 'buckets' in dist
    # At least one positive return bucket
    assert any(b['count'] > 0 for b in dist['buckets'])
    assert 'tail_left_count' in dist and 'tail_right_count' in dist and 'p90' in dist and 'p95' in dist


def test_position_size_series_monotonic_reductions():
    repo = _build_repo()
    series = position_size_series(repo.all())
    # Exposure should start positive after first BUY
    assert series[0]['gross_exposure'] > 0
    # Final exposure after all sells should be 0
    assert series[-1]['gross_exposure'] == 0


def test_return_distribution_empty():
    repo = TradeRepository()
    dist = return_distribution(repo.all())
    assert dist['count'] == 0 and dist['buckets'] == []


def test_holding_histogram_invalid_param():
    repo = TradeRepository()
    try:
        holding_duration_histogram(repo.all(), bucket_minutes=0)
        assert False, "Expected ValueError"
    except ValueError:
        pass
