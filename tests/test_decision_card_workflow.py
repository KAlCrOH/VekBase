"""
# ============================================================
# Context Banner — test_decision_card_workflow | Category: test
# Purpose: Validate DecisionCard status transitions and expiry computation.

# Contracts
#   - transition_status enforces allowed transitions
#   - ttl_days drives expires_at when approving

# Invariants
#   - Invalid transitions raise ValueError

# Dependencies
#   Internal: decision_card.transition_status, make_decision_card
#   External: stdlib (datetime)

# ============================================================
"""
from app.core.decision_card import make_decision_card, transition_status
from datetime import datetime, UTC, timedelta


def test_workflow_valid_approval_with_expiry():
    card = make_decision_card("wf1", author="me", title="T", action={"type": "hold", "ttl_days": 10})
    assert card.status == "draft"
    transition_status(card, "proposed", reviewer="rev1", now=datetime(2025,1,1, tzinfo=UTC))
    assert card.status == "proposed"
    assert "rev1" in card.reviewers
    transition_status(card, "approved", reviewer="rev2", now=datetime(2025,1,2, tzinfo=UTC))
    assert card.status == "approved"
    assert card.approved_at == datetime(2025,1,2, tzinfo=UTC)
    assert card.expires_at == datetime(2025,1,2, tzinfo=UTC) + timedelta(days=10)
    assert set(card.reviewers) == {"rev1","rev2"}


def test_workflow_rejection():
    card = make_decision_card("wf2", author="me", title="T")
    transition_status(card, "proposed", reviewer="r1")
    transition_status(card, "rejected", reviewer="r2")
    assert card.status == "rejected"
    assert "r1" in card.reviewers and "r2" in card.reviewers
    assert card.approved_at is None and card.expires_at is None


def test_workflow_invalid_transition():
    card = make_decision_card("wf3", author="me", title="T")
    try:
        transition_status(card, "approved")  # skipping proposed
        assert False, "Expected invalid transition error"
    except ValueError:
        pass
