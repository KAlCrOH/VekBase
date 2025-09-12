"""
# ============================================================
# Context Banner — test_decision_card | Category: test
# Purpose: Smoke-Test für DecisionCard Erstellung & Dictionary Serialisierung

# Contracts
#   Inputs: Parameter für make_decision_card
#   Outputs: Assertions auf Felder des Dictionary
#   Side-Effects: none
#   Determinism: deterministic (Zeitstempel nur auf Existenz geprüft)

# Invariants
#   - card_id & author erhalten

# Dependencies
#   Internal: core.decision_card
#   External: stdlib

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from app.core.decision_card import make_decision_card, ActionSpec


def test_decision_card_basic():
    card = make_decision_card("dc1", author="me", title="Test", action={"type": "hold"}, risks=["macro"], confidence=0.8)
    d = card.to_dict()
    assert d["card_id"] == "dc1"
    assert d["author"] == "me"
    assert "created_at" in d
    assert d["action"]["type"] == "hold"
    assert d["risks"] == ["macro"]
    assert abs(d["confidence"] - 0.8) < 1e-9


def test_decision_card_actionspec_direct():
    card = make_decision_card("dc2", author="a", title="T", action=ActionSpec(type="add", target_w=0.1, ttl_days=30))
    d = card.to_dict()
    assert d["action"]["type"] == "add"
    assert d["action"]["target_w"] == 0.1
    assert d["action"]["ttl_days"] == 30


def test_decision_card_invalid_confidence():
    try:
        make_decision_card("dc3", author="a", title="T", confidence=2.0)
        assert False, "Expected ValueError for confidence>1"
    except ValueError:
        pass


def test_decision_card_invalid_action_type():
    try:
        make_decision_card("dc4", author="a", title="T", action={"type": "xyz"})
        assert False, "Expected ValueError for invalid action type"
    except ValueError:
        pass