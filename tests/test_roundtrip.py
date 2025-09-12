"""
# ============================================================
# Context Banner — test_roundtrip | Category: test
# Purpose: Verifiziert CSV Export + Import (Roundtrip) und Positionsberechnung

# Contracts
#   Inputs: künstliche Trades -> Repo -> Export -> Reimport
#   Outputs: Assertions (Anzahl Trades, Positionswert)
#   Side-Effects: File I/O=write/read temp CSV
#   Determinism: deterministic

# Invariants
#   - Position nach Roundtrip identisch

# Dependencies
#   Internal: core.trade_repo, core.trade_model
#   External: stdlib (pathlib)

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from pathlib import Path
from app.core.trade_repo import TradeRepository
from app.core.trade_model import validate_trade_dict


def test_csv_roundtrip(tmp_path: Path):
    repo = TradeRepository()
    rows = [
        {"trade_id": "r1", "ts": "2024-01-01T09:00:00", "ticker": "XYZ", "action": "BUY", "shares": 2, "price": 10, "fees": 0},
        {"trade_id": "r2", "ts": "2024-01-02T09:00:00", "ticker": "XYZ", "action": "SELL", "shares": 1, "price": 11, "fees": 0.2},
    ]
    for r in rows:
        repo.add_trade(validate_trade_dict(r))
    out = tmp_path / "trades_out.csv"
    repo.export_csv(out)
    repo2 = TradeRepository()
    repo2.import_csv(out)
    assert len(repo2.all()) == 2
    assert repo2.positions()["XYZ"] == 1.0