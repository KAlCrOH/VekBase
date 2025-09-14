"""
# ============================================================
# Context Banner — test_unrealized_timeline | Category: test
# Purpose: Tests für unrealized_equity_timeline
# ============================================================
"""
from datetime import datetime, timedelta
from app.analytics.metrics import unrealized_equity_timeline
from app.core.trade_model import validate_trade_dict
from app.core.trade_repo import TradeRepository

def _repo():
    repo = TradeRepository()
    rows = [
        {"trade_id":"b1","ts":"2024-01-01T10:00:00","ticker":"AAA","action":"BUY","shares":5,"price":10,"fees":0},
        {"trade_id":"b2","ts":"2024-01-01T11:00:00","ticker":"AAA","action":"BUY","shares":5,"price":12,"fees":0},
        {"trade_id":"s1","ts":"2024-01-01T12:30:00","ticker":"AAA","action":"SELL","shares":4,"price":11,"fees":0},
    ]
    for r in rows:
        repo.add_trade(validate_trade_dict(r))
    return repo

def test_unrealized_timeline_basic():
    repo = _repo()
    marks = {"AAA": 13}
    timeline = unrealized_equity_timeline(repo.all(), mark_prices=marks)
    assert len(timeline) == 3
    # After first BUY unrealized positive when mark > price
    assert timeline[0][1] > 0
    # Monotonic not guaranteed but final value should reflect remaining 6 shares (5+5-4) at avg cost  (50+60-portion) -> remaining lots 1@10,5@12 unrealized (13-10)*1 + (13-12)*5 = 3+5 =8
    assert abs(timeline[-1][1] - 8) < 1e-9

def test_unrealized_timeline_with_now_extension():
    repo = _repo()
    marks = {"AAA": 14}
    now = datetime(2024,1,1,13,0,0)
    timeline = unrealized_equity_timeline(repo.all(), mark_prices=marks, now=now)
    assert timeline[-1][0] == now
    # Compute final: remaining 6 shares (1@10,5@12) -> (14-10)*1 + (14-12)*5 = 4 + 10 =14
    assert abs(timeline[-1][1] - 14) < 1e-9

def test_unrealized_timeline_no_marks():
    repo = _repo()
    timeline = unrealized_equity_timeline(repo.all(), mark_prices={})
    assert timeline == []
