from app.core.trade_model import validate_trade_dict, TradeValidationError
from datetime import datetime

def test_validate_ok():
    raw = {
        "trade_id": "t1",
        "ts": "2024-01-01T10:00:00",
        "ticker": "NVDA",
        "action": "BUY",
        "shares": 10,
        "price": 100,
        "fees": 1.5,
    }
    t = validate_trade_dict(raw)
    assert t.ticker == "NVDA"
    assert t.fees == 1.5


def test_validate_missing():
    raw = {"trade_id": "t2"}
    try:
        validate_trade_dict(raw)
        assert False, "should fail"
    except TradeValidationError:
        pass
