"""
# ============================================================
# Context Banner — default_data | Category: core
# Purpose: Bereitstellung eines kleinen synthetischen Default-Datensatzes (mehrere Ticker, Long/Teilverkäufe) für UI Visualisierungen.
# Contracts
#   load_default_trades(repo: TradeRepository) -> int (Anzahl hinzugefügter Trades)
# Invariants
#   - Deterministisch
#   - Keine externen I/O Seiten-Effekte
# ============================================================
"""
from __future__ import annotations
from datetime import datetime, timedelta
from .trade_model import validate_trade_dict
from .trade_repo import TradeRepository

_DEF_ROWS = []
_base = datetime(2024,1,1,9,0,0)
# Ticker AAA: round trip + partial
_DEF_ROWS += [
    {"trade_id":"AAA_b1","ts":(_base).isoformat(),"ticker":"AAA","action":"BUY","shares":10,"price":100.0,"fees":0},
    {"trade_id":"AAA_b2","ts":(_base+timedelta(hours=2)).isoformat(),"ticker":"AAA","action":"BUY","shares":5,"price":102.0,"fees":0},
    {"trade_id":"AAA_s1","ts":(_base+timedelta(days=1)).isoformat(),"ticker":"AAA","action":"SELL","shares":8,"price":108.0,"fees":0},
    {"trade_id":"AAA_s2","ts":(_base+timedelta(days=2)).isoformat(),"ticker":"AAA","action":"SELL","shares":7,"price":105.0,"fees":0},
]
# Ticker BBB: partial sell leaving open position
_DEF_ROWS += [
    {"trade_id":"BBB_b1","ts":(_base+timedelta(minutes=30)).isoformat(),"ticker":"BBB","action":"BUY","shares":6,"price":50.0,"fees":0},
    {"trade_id":"BBB_b2","ts":(_base+timedelta(hours=5)).isoformat(),"ticker":"BBB","action":"BUY","shares":4,"price":49.0,"fees":0},
    {"trade_id":"BBB_s1","ts":(_base+timedelta(days=1, hours=1)).isoformat(),"ticker":"BBB","action":"SELL","shares":5,"price":55.0,"fees":0},
]
# Ticker PAT: small pattern dataset
_DEF_ROWS += [
    {"trade_id":"PAT_b1","ts":(_base+timedelta(days=3)).isoformat(),"ticker":"PAT","action":"BUY","shares":5,"price":10.0,"fees":0},
    {"trade_id":"PAT_b2","ts":(_base+timedelta(days=3, hours=1)).isoformat(),"ticker":"PAT","action":"BUY","shares":5,"price":11.0,"fees":0},
    {"trade_id":"PAT_s1","ts":(_base+timedelta(days=3, hours=4)).isoformat(),"ticker":"PAT","action":"SELL","shares":6,"price":12.0,"fees":0},
]


def load_default_trades(repo: TradeRepository) -> int:
    count = 0
    existing_ids = {t.trade_id for t in repo.all()}
    for r in _DEF_ROWS:
        if r["trade_id"] in existing_ids:
            continue
        repo.add_trade(validate_trade_dict(r))
        count += 1
    return count

__all__ = ["load_default_trades"]
