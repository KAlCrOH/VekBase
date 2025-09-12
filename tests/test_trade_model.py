"""
# ============================================================
# Context Banner — test_trade_model | Category: test
# Purpose: Tests für Trade Validierung (Happy Path + Fehlende Felder Negativfall)

# Contracts
#   Inputs: raw dicts simuliert CSV/Manuelle Eingabe
#   Outputs: Assertions auf Trade Objekt oder Exception
#   Side-Effects: none
#   Determinism: deterministic

# Invariants
#   - Prüft Pflichtfelder & Fehlermeldung

# Dependencies
#   Internal: core.trade_model
#   External: stdlib

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
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
