# ============================================================
# Context Banner — decision_card | Category: core
# Purpose: Lightweight DecisionCard Dataclass zur Dokumentation von Annahmen & Entscheidungen (ADR-Light)
# Note: Spec (CONTEXT/05_DECISION_CARD_SPEC.md) beschreibt zusätzliche Felder (action{type,target_w,ttl_days}, risks, confidence) – Diese wurden jetzt implementiert (Increment: prompt3_roadmap_implement)

# Contracts
#   Inputs: make_decision_card(card_id, author, title, **optional_fields)
#   Outputs: DecisionCard Instanz (to_dict serialisiert ISO timestamps)
#   Side-Effects: File I/O=none; Network=none
#   Determinism: deterministic (Zeit via datetime.utcnow() – austauschbar für UTC aware)

# Invariants
#   - Keine Logik jenseits reiner Datenhaltung
#   - Erweiterbar um Evaluations-/Review Felder

# Dependencies
#   Internal: none (kann mit analytics Snapshot kombiniert werden)
#   External: stdlib (dataclasses, datetime, typing)

# Tests
#   tests/test_decision_card.py

# Do-Not-Change
#   Banner policy-relevant; Änderungen nur via Task „Header aktualisieren“.
# ============================================================
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import List, Dict, Any


@dataclass
class ActionSpec:
    """Lightweight embedded action recommendation.
    type: hold|add|trim|exit
    target_w: Ziel-Gewicht (0..1 oder >1 falls Prozentpunkte) – hier nur >=0 validiert.
    ttl_days: Empfohlene Gültigkeit in Tagen.
    """
    type: str
    target_w: float | None = None
    ttl_days: int | None = None

    def validate(self) -> None:
        """Business validation for action spec.
        Rules (increment: action_validation):
          - type ∈ {hold, add, trim, exit}
          - target_w:
              * required for add / trim (explicit sizing)
              * optional for hold (keine Größenänderung) und exit (impliziert Ziel 0)
              * if provided: >= 0
          - ttl_days if provided must be >= 1 (0 macht semantisch keinen Sinn)
        """
        allowed = {"hold", "add", "trim", "exit"}
        if self.type not in allowed:
            raise ValueError(f"action.type invalid: {self.type} not in {allowed}")
        # target_w presence rules
        if self.type in {"add", "trim"} and self.target_w is None:
            raise ValueError("action.target_w required for add/trim")
        if self.type == "exit" and self.target_w is not None and self.target_w != 0:
            # exit implies going to zero; allow explicit 0 but reject other numbers
            raise ValueError("action.target_w for exit must be omitted or 0")
        if self.target_w is not None and self.target_w < 0:
            raise ValueError("action.target_w must be >= 0")
        if self.ttl_days is not None and self.ttl_days < 1:
            raise ValueError("action.ttl_days must be >= 1")

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in {
            "type": self.type,
            "target_w": self.target_w,
            "ttl_days": self.ttl_days,
        }.items() if v is not None}


@dataclass
class DecisionCard:
    card_id: str
    created_at: datetime
    author: str
    title: str
    context_refs: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    options: List[str] = field(default_factory=list)
    decision: str | None = None
    rationale: str | None = None
    metrics_snapshot: Dict[str, Any] | None = None
    # NEW FIELDS (Increment prompt3_roadmap_implement)
    action: ActionSpec | None = None
    risks: List[str] = field(default_factory=list)
    confidence: float | None = None  # 0..1
    # WORKFLOW FIELDS (Increment action_validation + workflow)
    status: str = "draft"  # draft -> proposed -> approved | rejected
    reviewers: List[str] = field(default_factory=list)
    approved_at: datetime | None = None
    expires_at: datetime | None = None  # derived from ttl_days of action when approved

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card_id": self.card_id,
            "created_at": self.created_at.isoformat(),
            "author": self.author,
            "title": self.title,
            "context_refs": self.context_refs,
            "assumptions": self.assumptions,
            "options": self.options,
            "decision": self.decision,
            "rationale": self.rationale,
            "metrics_snapshot": self.metrics_snapshot,
            "action": self.action.to_dict() if self.action else None,
            "risks": self.risks,
            "confidence": self.confidence,
            "status": self.status,
            "reviewers": self.reviewers,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


def _build_action(raw: Dict[str, Any] | ActionSpec | None) -> ActionSpec | None:
    if raw is None:
        return None
    if isinstance(raw, ActionSpec):
        raw.validate()
        return raw
    if not isinstance(raw, dict):  # defensive
        raise ValueError("action must be dict or ActionSpec")
    spec = ActionSpec(
        type=raw.get("type", "hold"),
        target_w=raw.get("target_w"),
        ttl_days=raw.get("ttl_days"),
    )
    spec.validate()
    return spec


def make_decision_card(card_id: str, author: str, title: str, **kwargs) -> DecisionCard:
    """Factory with validation for optional fields.
    Backward compatible: ignores unknown kwargs silently (policy: defensive filtering).
    Validation rules:
      - confidence in [0,1]
      - risks must be list[str]
      - action validated via ActionSpec
    """
    allowed = {'context_refs','assumptions','options','decision','rationale','metrics_snapshot','action','risks','confidence','status','reviewers'}
    filtered: Dict[str, Any] = {k: v for k, v in kwargs.items() if k in allowed}

    # normalize & validate new fields
    action_obj = _build_action(filtered.get('action')) if 'action' in filtered else None
    risks_val = filtered.get('risks') if 'risks' in filtered else []
    if risks_val and (not isinstance(risks_val, list) or any(not isinstance(r, str) for r in risks_val)):
        raise ValueError("risks must be list[str]")
    confidence_val = filtered.get('confidence') if 'confidence' in filtered else None
    if confidence_val is not None:
        try:
            cf = float(confidence_val)
        except Exception as e:
            raise ValueError("confidence must be float 0..1") from e
        if cf < 0 or cf > 1:
            raise ValueError("confidence must be between 0 and 1")
        confidence_val = cf

    status_val = filtered.get('status', 'draft')
    if status_val not in {"draft","proposed","approved","rejected"}:
        raise ValueError("status invalid")
    reviewers_val = filtered.get('reviewers', [])
    if reviewers_val and (not isinstance(reviewers_val, list) or any(not isinstance(r, str) for r in reviewers_val)):
        raise ValueError("reviewers must be list[str]")

    return DecisionCard(
        card_id=card_id,
    created_at=datetime.now(UTC),
        author=author,
        title=title,
        context_refs=filtered.get('context_refs', []),
        assumptions=filtered.get('assumptions', []),
        options=filtered.get('options', []),
        decision=filtered.get('decision'),
        rationale=filtered.get('rationale'),
        metrics_snapshot=filtered.get('metrics_snapshot'),
        action=action_obj,
        risks=risks_val or [],
        confidence=confidence_val,
        status=status_val,
        reviewers=reviewers_val or [],
    )


def transition_status(card: DecisionCard, new_status: str, reviewer: str | None = None, now: datetime | None = None) -> DecisionCard:
    """Perform workflow transition with validation.
    Allowed transitions:
        draft -> proposed
        proposed -> approved | rejected
    No other transitions permitted (idempotent same-status allowed).
    When approving: sets approved_at and, if action.ttl_days present, computes expires_at = approved_at + ttl_days.
    Reviewer appended if provided and not already listed.
    Returns mutated card (in-place change for simplicity) and also returns it for chaining.
    Pure except for datetime capture.
    """
    allowed_status = {"draft","proposed","approved","rejected"}
    if new_status not in allowed_status:
        raise ValueError("new_status invalid")
    if card.status == new_status:
        # idempotent
        if reviewer and reviewer not in card.reviewers:
            card.reviewers.append(reviewer)
        return card
    if card.status == "draft" and new_status == "proposed":
        card.status = "proposed"
    elif card.status == "proposed" and new_status in {"approved","rejected"}:
        card.status = new_status
        if new_status == "approved":
            ts = now or datetime.now(UTC)
            card.approved_at = ts
            if card.action and card.action.ttl_days:
                from datetime import timedelta
                card.expires_at = ts + timedelta(days=card.action.ttl_days)
    else:
        raise ValueError(f"invalid transition {card.status} -> {new_status}")
    if reviewer and reviewer not in card.reviewers:
        card.reviewers.append(reviewer)
    return card

# Explicit exports
__all__ = [
    'ActionSpec','DecisionCard','make_decision_card','transition_status'
]
