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
        allowed = {"hold", "add", "trim", "exit"}
        if self.type not in allowed:
            raise ValueError(f"action.type invalid: {self.type} not in {allowed}")
        if self.target_w is not None and self.target_w < 0:
            raise ValueError("action.target_w must be >= 0")
        if self.ttl_days is not None and self.ttl_days < 0:
            raise ValueError("action.ttl_days must be >= 0")

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
    allowed = {'context_refs','assumptions','options','decision','rationale','metrics_snapshot','action','risks','confidence'}
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
    )
