"""
# ============================================================
# Context Banner — test_default_dataset | Category: test
# Purpose: Verifiziert Laden des Default-Datensatzes (synthetische Trades) bei leerem Repo.
# ============================================================
"""
from app.core.trade_repo import TradeRepository
from app.core.default_data import load_default_trades


def test_load_default_trades_idempotent():
    repo = TradeRepository()
    added_first = load_default_trades(repo)
    assert added_first > 0
    count_after_first = len(repo.all())
    added_second = load_default_trades(repo)
    # second load must not duplicate
    assert added_second == 0
    assert len(repo.all()) == count_after_first
