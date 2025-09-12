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


def test_retrieval_keyword():
    files = retrieval.list_context_files()
    if not files:
        return  # skip silently if docs missing
    res = retrieval.retrieve('projekt')  # german word likely in charter
    assert isinstance(res, list)
    if res:
        assert 'file' in res[0]