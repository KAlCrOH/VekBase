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
from app.core.decision_card import make_decision_card


def test_decision_card_basic():
    card = make_decision_card("dc1", author="me", title="Test")
    d = card.to_dict()
    assert d["card_id"] == "dc1"
    assert d["author"] == "me"
    assert "created_at" in d