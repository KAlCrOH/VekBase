"""
# ============================================================
# Context Banner — test_admin_features | Category: test
# Purpose: Tests für Admin Feature Wrapper (Retrieval & DecisionCards)

# Contracts
#   - retrieve_context liefert Liste (>=0) von dicts mit keys file, score, snippet
#   - create_decision_card legt Karte persistiert an; list_decision_cards spiegelt sie

# Invariants
#   - Kein Netzwerk
#   - Deterministische Ergebnisse für gleiche Inputs

# Dependencies
#   Internal: app.ui.admin_feature_wrappers
#   External: stdlib

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from app.ui import admin_feature_wrappers as feat
from pathlib import Path


def test_retrieval_wrapper_smoke():
    res = feat.retrieve_context("projekt", limit=2)
    # May be empty but should be list
    assert isinstance(res, list)
    if res:
        assert set(res[0].keys()) >= {"file","score","snippet"}


def test_decision_card_create_and_list(tmp_path, monkeypatch):
    # Use temp path to avoid polluting repo data
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    card = feat.create_decision_card("data/decision_cards.json", card_id="dc_test_1", author="me", title="Test Card", action={"type":"hold"})
    assert card["card_id"] == "dc_test_1"
    listed = feat.list_decision_cards("data/decision_cards.json")
    assert any(c["card_id"]=="dc_test_1" for c in listed)