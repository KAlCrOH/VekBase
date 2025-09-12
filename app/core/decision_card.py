# ============================================================
# Context Banner — decision_card | Category: core
# Purpose: Lightweight DecisionCard Dataclass zur Dokumentation von Annahmen & Entscheidungen (ADR-Light)

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
from datetime import datetime
from typing import List, Dict, Any


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
        }


def make_decision_card(card_id: str, author: str, title: str, **kwargs) -> DecisionCard:
    return DecisionCard(
        card_id=card_id,
        created_at=datetime.utcnow(),
        author=author,
        title=title,
        **{k: v for k, v in kwargs.items() if k in {
            'context_refs','assumptions','options','decision','rationale','metrics_snapshot'
        }}
    )
