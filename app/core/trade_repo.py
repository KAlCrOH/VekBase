"""In-memory trade repository with CSV load/save and position validation.
No external deps. All I/O explicit. Positions computed on demand.
"""
from __future__ import annotations
from typing import List, Dict, Iterable, Optional
from dataclasses import dataclass
import csv
from pathlib import Path
from .trade_model import Trade, validate_trade_dict, TradeValidationError

@dataclass
class PositionLot:
    ticker: str
    shares: float

class TradeRepository:
    def __init__(self):
        self._trades: List[Trade] = []
        self._index: Dict[str, Trade] = {}

    def add_trade(self, trade: Trade) -> None:
        if trade.trade_id in self._index:
            raise TradeValidationError(f"duplicate trade_id {trade.trade_id}")
        # enforce monotonic time per ticker (simpler than per trade_id which is unique anyway)
        prev = [t for t in self._trades if t.ticker == trade.ticker]
        if prev and any(trade.ts < t.ts for t in prev):
            raise TradeValidationError("timestamp monotonicity violated for ticker")
        # position constraint for SELL
        if trade.action == "SELL":
            pos = self.position_for(trade.ticker)
            if pos < trade.shares:
                raise TradeValidationError("SELL would create negative position")
        self._trades.append(trade)
        self._index[trade.trade_id] = trade

    def add_many(self, trades: Iterable[Trade]) -> None:
        for t in trades:
            self.add_trade(t)

    def all(self) -> List[Trade]:
        return list(self._trades)

    def by_ticker(self, ticker: str) -> List[Trade]:
        up = ticker.upper()
        return [t for t in self._trades if t.ticker == up]

    def position_for(self, ticker: str) -> float:
        qty = 0.0
        for t in self.by_ticker(ticker):
            if t.action == "BUY":
                qty += t.shares
            else:
                qty -= t.shares
        return qty

    def positions(self) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for t in self._trades:
            out.setdefault(t.ticker, 0.0)
            if t.action == "BUY":
                out[t.ticker] += t.shares
            else:
                out[t.ticker] -= t.shares
        return out

    # CSV I/O
    @staticmethod
    def load_csv(path: Path) -> List[Dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [row for row in reader]

    def import_csv(self, path: Path) -> None:
        rows = self.load_csv(path)
        trades = [validate_trade_dict(r) for r in rows]
        # ensure sorted by ts for monotonicity convenience
        trades.sort(key=lambda t: t.ts)
        self.add_many(trades)

    def export_csv(self, path: Path) -> None:
        if not self._trades:
            return
        fieldnames = list(self._trades[0].to_dict().keys())
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for t in self._trades:
                w.writerow(t.to_dict())
