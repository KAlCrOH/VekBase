"""
# ============================================================
# Context Banner — test_decision_card_repo | Category: test
# Purpose: Verifiziert DecisionCardRepository Persistenz & Validierungen

# Contracts
#   add/get/all/save/load uniqueness + reconstruction

# Dependencies
#   Internal: decision_card_repo, decision_card
#   External: stdlib (tempfile, pathlib, json)

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from app.core.decision_card_repo import DecisionCardRepository
from app.core.decision_card import make_decision_card
from pathlib import Path
import json


def test_repo_add_save_load(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    repo = DecisionCardRepository("data/decision_cards.json")
    card = make_decision_card("c1", author="me", title="Test", assumptions=["A1"], action={"type":"hold"}, confidence=0.8)
    repo.add(card)
    repo.save()
    assert (tmp_path/"data/decision_cards.json").exists()
    # reload new repo
    repo2 = DecisionCardRepository("data/decision_cards.json")
    assert repo2.get("c1") is not None
    assert repo2.all()[0].title == "Test"


def test_repo_duplicate_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    repo = DecisionCardRepository("data/decision_cards.json")
    card1 = make_decision_card("dup", author="me", title="One")
    repo.add(card1)
    try:
        repo.add(make_decision_card("dup", author="me", title="Two"))
        assert False, "Expected duplicate id error"
    except ValueError as e:
        assert "already exists" in str(e)
