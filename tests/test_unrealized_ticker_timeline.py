"""
# ============================================================
# Context Banner — test_unrealized_ticker_timeline | Category: test
# Purpose: Tests für unrealized_equity_timeline_by_ticker
# ============================================================
"""
from datetime import datetime
from app.analytics.metrics import unrealized_equity_timeline_by_ticker
from app.core.trade_model import validate_trade_dict
from app.core.trade_repo import TradeRepository

def _repo_multi():
    repo = TradeRepository()
    rows = [
        {"trade_id":"a1","ts":"2024-01-01T10:00:00","ticker":"AAA","action":"BUY","shares":5,"price":10,"fees":0},
        {"trade_id":"b1","ts":"2024-01-01T10:05:00","ticker":"BBB","action":"BUY","shares":3,"price":20,"fees":0},
        {"trade_id":"a2","ts":"2024-01-01T11:00:00","ticker":"AAA","action":"BUY","shares":5,"price":12,"fees":0},
        {"trade_id":"b2","ts":"2024-01-01T11:30:00","ticker":"BBB","action":"SELL","shares":1,"price":22,"fees":0},
        {"trade_id":"a3","ts":"2024-01-01T12:00:00","ticker":"AAA","action":"SELL","shares":4,"price":11,"fees":0},
    ]
    for r in rows:
        repo.add_trade(validate_trade_dict(r))
    return repo

def test_per_ticker_unrealized_basic():
    repo = _repo_multi()
    marks = {"AAA": 14, "BBB": 25}
    tl = unrealized_equity_timeline_by_ticker(repo.all(), marks)
    assert 'AAA' in tl and 'BBB' in tl
    assert tl['AAA'][-1][1] > 0
    # BBB has sold 1 share, remaining 2 shares at 20 cost each unrealized (25-20)*2 = 10
    assert abs(tl['BBB'][-1][1] - 10) < 1e-9

def test_per_ticker_now_extension():
    repo = _repo_multi()
    marks = {"AAA": 13}
    now = datetime(2024,1,1,13,0,0)
    tl = unrealized_equity_timeline_by_ticker(repo.all(), marks, now=now)
    assert tl['AAA'][-1][0] == now

def test_per_ticker_missing_marks():
    repo = _repo_multi()
    tl = unrealized_equity_timeline_by_ticker(repo.all(), {})
    assert tl == {}
