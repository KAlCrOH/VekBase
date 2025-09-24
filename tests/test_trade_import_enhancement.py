"""Tests for trade import enhancement helpers (schema + diff)."""
from app.core.trade_model import Trade
from app.core.trade_import import infer_csv_schema, parse_csv_text, diff_trades
from datetime import datetime

SAMPLE_CSV = """trade_id,ts,ticker,action,shares,price,fees,tag\n""" \
             """t1,2024-01-01T09:00:00,ABC,BUY,10,5.0,0.1,alpha\n""" \
             """t2,2024-01-01T10:00:00,ABC,SELL,5,5.5,0.1,beta\n"""

def make_trade(tid: str) -> Trade:
    return Trade(
        trade_id=tid,
        ts=datetime(2024,1,1,9,0,0),
        ticker="ABC",
        action="BUY",
        shares=10.0,
        price=5.0,
        fees=0.1,
    )


def test_infer_schema_valid():
    res = infer_csv_schema(SAMPLE_CSV)
    assert res["valid"] is True
    assert not res["required_missing"]
    assert "trade_id" in res["header"]
    assert res["row_count"] == 2


def test_parse_csv_text():
    rows = parse_csv_text(SAMPLE_CSV)
    assert len(rows) == 2
    assert rows[0]["trade_id"] == "t1"


def test_diff_trades_new_and_changed():
    existing = [make_trade("t1")]
    rows = parse_csv_text(SAMPLE_CSV)
    # Modify one row to simulate change
    rows[0]["price"] = "6.0"  # changed vs existing (5.0)
    d = diff_trades(existing, rows)
    assert "t2" in d["new_ids"]  # new trade
    assert "t1" in d["changed"]  # changed price
    assert d["importable_count"] == 1  # only t2 is importable


def test_diff_trades_duplicates():
    csv_dup = "trade_id,ts,ticker,action,shares,price\n" \
              "x1,2024-01-01T09:00:00,ABC,BUY,1,1.0\n" \
              "x1,2024-01-01T10:00:00,ABC,BUY,1,1.0\n"
    rows = parse_csv_text(csv_dup)
    d = diff_trades([], rows)
    assert "x1" in d["duplicate_ids"]
    assert d["importable_count"] == 1  # first counts, second duplicate skipped
