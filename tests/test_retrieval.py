"""
# ============================================================
# Context Banner — test_retrieval | Category: test
# Purpose: Smoke-Test für lokalen Keyword Retrieval Stub

# Contracts
#   Inputs: Query 'projekt' + vorhandene Kontext-Dateien
#   Outputs: Liste Treffer oder leer
#   Side-Effects: File I/O=read docs/CONTEXT/*.md
#   Determinism: deterministic relativ zum Dateisystem

# Invariants
#   - Keine Netzaufrufe

# Dependencies
#   Internal: core.retrieval
#   External: stdlib

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from app.core import retrieval
from datetime import date


def test_retrieval_keyword():
    files = retrieval.list_context_files()
    if not files:
        return  # skip silently if docs missing
    res = retrieval.retrieve('projekt')  # german word likely in charter
    assert isinstance(res, list)
    if res:
        assert 'file' in res[0]


def test_retrieval_with_ticker_filter_no_match():
    files = retrieval.list_context_files()
    if not files:
        return
    res = retrieval.retrieve('projekt', ticker='NONEXISTENTTICKER')
    # Should be empty because ticker substring not in docs
    assert res == []


def test_retrieval_with_as_of_filter():
    files = retrieval.list_context_files()
    if not files:
        return
    # Using today's date ensures existing context files (with any earlier iso date mentions) pass heuristic
    res = retrieval.retrieve('projekt', as_of=date.today())
    assert isinstance(res, list)