"""
# ============================================================
# Context Banner — test_rolling_volatility | Category: test
# Purpose: Tests für rolling_volatility
# ============================================================
"""
from datetime import datetime, timedelta
from app.analytics.metrics import rolling_volatility

def _curve():
    base = datetime(2024,1,1,10,0,0)
    vals = [0,10,12,9,15,16,14]
    return [(base + timedelta(minutes=i), v) for i,v in enumerate(vals)]


def test_rolling_volatility_basic():
    curve = _curve()
    rv = rolling_volatility(curve, window=3)
    assert len(rv) == len(curve)
    # first two should be None
    assert rv[0]['vol'] is None and rv[1]['vol'] is None
    # later entries have numeric vol
    assert any(isinstance(x['vol'], float) for x in rv[3:])


def test_rolling_volatility_invalid():
    try:
        rolling_volatility([], window=3)
    except Exception:
        pass
    try:
        rolling_volatility(_curve(), window=1)
        assert False, "Expected ValueError for window=1"
    except ValueError:
        pass
