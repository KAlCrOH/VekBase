"""
# ============================================================
# Context Banner — decision_card_repo | Category: core
# Purpose: JSON Persistenz für DecisionCards (Append/Replace Strategie) – speichert unter data/decision_cards.json.

# Contracts
#   DecisionCardRepository(path: Path|str = 'data/decision_cards.json')
#     .add(card: DecisionCard) -> None  (card_id uniqueness enforced)
#     .all() -> list[DecisionCard]
#     .get(card_id) -> DecisionCard | None
#     .save() -> None  (writes JSON array of card dicts)
#     .load() -> None  (idempotent; loads if file exists)

# Invariants
#   - Keine stillen Formatänderungen: Schema = Liste von Objekten wie DecisionCard.to_dict
#   - Doppelte card_id verweigert (ValueError)
#   - Deterministisch (Reihenfolge = Insert Reihenfolge)

# Dependencies
#   Internal: decision_card.make_decision_card / DecisionCard
#   External: stdlib

# Tests
#   tests/test_decision_card_repo.py

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional
import json
from .decision_card import DecisionCard, make_decision_card, ActionSpec
from datetime import datetime


class DecisionCardRepository:
    def __init__(self, path: str | Path = "data/decision_cards.json") -> None:
        self.path = Path(path)
        self._cards: List[DecisionCard] = []
        self.load()

    def add(self, card: DecisionCard) -> None:
        if any(c.card_id == card.card_id for c in self._cards):
            raise ValueError(f"card_id already exists: {card.card_id}")
        self._cards.append(card)

    def all(self) -> List[DecisionCard]:
        return list(self._cards)

    def get(self, card_id: str) -> Optional[DecisionCard]:
        return next((c for c in self._cards if c.card_id == card_id), None)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [c.to_dict() for c in self._cards]
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return  # ignore corrupt file silently (KISS) – could be extended
        out: List[DecisionCard] = []
        for obj in data:
            # reconstruct action spec if present
            action = obj.get("action")
            from .decision_card import _build_action  # local import to avoid cycle at top level
            action_spec = _build_action(action) if action else None
            # created_at iso parse
            try:
                created_at = datetime.fromisoformat(obj.get("created_at"))
            except Exception:
                continue
            card = DecisionCard(
                card_id=obj.get("card_id"),
                created_at=created_at,
                author=obj.get("author"),
                title=obj.get("title"),
                context_refs=obj.get("context_refs", []),
                assumptions=obj.get("assumptions", []),
                options=obj.get("options", []),
                decision=obj.get("decision"),
                rationale=obj.get("rationale"),
                metrics_snapshot=obj.get("metrics_snapshot"),
                action=action_spec,
                risks=obj.get("risks", []),
                confidence=obj.get("confidence"),
            )
            out.append(card)
        self._cards = out
