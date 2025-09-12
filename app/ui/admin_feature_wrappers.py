"""
# ============================================================
# Context Banner — admin_feature_wrappers | Category: ui
# Purpose: Streamlit-unabhängige Wrapper für Retrieval & DecisionCards zur Nutzung im Admin UI.

# Contracts
#   retrieve_context(query:str, limit:int=3, ticker:str|None=None, as_of:str|None=None) -> list[dict]
#   list_decision_cards(path='data/decision_cards.json') -> list[dict]
#   create_decision_card(repo_path, **fields) -> dict (persisted)

# Invariants
#   - Keine Netzwerkzugriffe
#   - Reine Delegation an core.retrieval & decision_card_repo
#   - Deterministische Ausgabe für gleiche Eingaben

# Dependencies
#   Internal: app.core.retrieval, app.core.decision_card_repo, app.core.decision_card
#   External: stdlib only

# Tests
#   tests/test_admin_features.py

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from pathlib import Path
from app.core import retrieval as _retr
from app.core.decision_card_repo import DecisionCardRepository
from app.core.decision_card import make_decision_card


def retrieve_context(query: str, limit: int = 3, ticker: Optional[str] = None, as_of: Optional[str] = None) -> List[Dict[str, str]]:
    return _retr.retrieve(query=query, limit=limit, ticker=ticker, as_of=as_of)


def list_decision_cards(path: str | Path = "data/decision_cards.json") -> List[Dict[str, Any]]:
    repo = DecisionCardRepository(path)
    return [c.to_dict() for c in repo.all()]


def create_decision_card(path: str | Path, card_id: str, author: str, title: str, **kwargs) -> Dict[str, Any]:
    repo = DecisionCardRepository(path)
    card = make_decision_card(card_id=card_id, author=author, title=title, **kwargs)
    repo.add(card)
    repo.save()
    return card.to_dict()


__all__ = ["retrieve_context", "list_decision_cards", "create_decision_card"]
