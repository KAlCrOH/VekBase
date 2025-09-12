from app.core.decision_card import make_decision_card


def test_decision_card_basic():
    card = make_decision_card("dc1", author="me", title="Test")
    d = card.to_dict()
    assert d["card_id"] == "dc1"
    assert d["author"] == "me"
    assert "created_at" in d