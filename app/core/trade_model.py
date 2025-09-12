"""Trade data model and validation.
Context derived from `docs/CONTEXT/04_DATA_SCHEMA_TRADES.md`.
Klarheit vor Cleverness: simple dataclass + explicit validate function.
No hidden I/O, pure functions for validation.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any

ISO_FORMATS = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]  # allow T or space

ACTIONS = {"BUY", "SELL"}

@dataclass(frozen=True)
class Trade:
    trade_id: str
    ts: datetime
    ticker: str
    action: str  # BUY | SELL
    shares: float
    price: float
    fees: float = 0.0
    tag: Optional[str] = None
    note_path: Optional[str] = None
    account: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["ts"] = self.ts.isoformat()
        return d

def parse_ts(value: str) -> datetime:
    for fmt in ISO_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    # allow full isoformat fallback
    try:
        return datetime.fromisoformat(value)
    except ValueError as e:
        raise ValueError(f"Invalid datetime format: {value}") from e

class TradeValidationError(ValueError):
    pass

def validate_trade_dict(raw: Dict[str, Any]) -> Trade:
    """Validate raw dict (e.g., from CSV) and return Trade.
    Required: trade_id, ts, ticker, action, shares, price, fees(optional default 0)
    Optional: tag, note_path, account
    """
    missing = [k for k in ["trade_id", "ts", "ticker", "action", "shares", "price"] if k not in raw or raw[k] in (None, "")]
    if missing:
        raise TradeValidationError(f"Missing required fields: {missing}")

    action = raw["action"].upper().strip()
    if action not in ACTIONS:
        raise TradeValidationError(f"Invalid action: {action}")

    try:
        shares = float(raw["shares"])
    except Exception as e:
        raise TradeValidationError("shares not numeric") from e
    if shares <= 0:
        raise TradeValidationError("shares must be > 0")

    try:
        price = float(raw["price"])
    except Exception as e:
        raise TradeValidationError("price not numeric") from e
    if price < 0:
        raise TradeValidationError("price must be >= 0")

    fees_raw = raw.get("fees", 0.0) or 0.0
    try:
        fees = float(fees_raw)
    except Exception as e:
        raise TradeValidationError("fees not numeric") from e
    if fees < 0:
        raise TradeValidationError("fees must be >= 0")

    ts = raw["ts"]
    if isinstance(ts, datetime):
        dt = ts
    else:
        dt = parse_ts(str(ts))

    trade = Trade(
        trade_id=str(raw["trade_id"]).strip(),
        ts=dt,
        ticker=str(raw["ticker"]).strip().upper(),
        action=action,
        shares=shares,
        price=price,
        fees=fees,
        tag=(str(raw["tag"]).strip() if raw.get("tag") else None),
        note_path=(str(raw["note_path"]).strip() if raw.get("note_path") else None),
        account=(str(raw["account"]).strip() if raw.get("account") else None),
    )
    return trade
