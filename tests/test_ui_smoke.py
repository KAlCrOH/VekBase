"""
# ============================================================
# Context Banner — test_ui_smoke | Category: test
# Purpose: End-to-end lightweight smoke for UI feature wrappers (retrieval advanced scoring + decision card lifecycle).
#
# Contracts
#   - retrieval.retrieve with advanced flag returns list (>=0)
#   - create_decision_card then list_decision_cards returns the created card
#   - Advanced scoring does not throw and yields integer score strings
#
# Invariants
#   - No network
#   - Deterministic for stable docs content
#
# Dependencies
#   Internal: app.ui.admin_feature_wrappers, app.core.retrieval
#   External: stdlib
#
# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from pathlib import Path
from app.ui import admin_feature_wrappers as feat
from app.core import retrieval


def test_ui_smoke_retrieval_and_decision_card(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Create minimal docs context file to ensure a hit
    docs_dir = Path('docs/CONTEXT')
    docs_dir.mkdir(parents=True, exist_ok=True)
    sample = docs_dir / '00_TEST_DOC.md'
    sample.write_text('# Title\nProjekt Beschreibung Projekt Projekt', encoding='utf-8')

    # Basic retrieval
    basic = retrieval.retrieve('projekt', limit=5, advanced=False)
    adv = retrieval.retrieve('projekt', limit=5, advanced=True)
    assert isinstance(basic, list) and isinstance(adv, list)
    if adv:
        assert all('score' in r for r in adv)
        # Advanced scores should be >= basic score for at least one index (boost)
        if basic:
            import itertools
            paired = list(itertools.zip_longest(basic, adv, fillvalue=None))
            assert any(int((b or {'score':0})['score']) <= int((a or {'score':0})['score']) for b, a in paired if a)

    # Decision card lifecycle
    repo_path = Path('data/decision_cards.json')
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    card = feat.create_decision_card(repo_path, card_id='dc_ui_smoke', author='tester', title='UI Smoke Card', action={'type':'hold'})
    assert card['card_id'] == 'dc_ui_smoke'
    listed = feat.list_decision_cards(repo_path)
    assert any(c['card_id']=='dc_ui_smoke' for c in listed)
