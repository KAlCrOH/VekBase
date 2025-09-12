"""
# ============================================================
# Context Banner — snapshots | Category: core
# Purpose: Deterministisches Snapshot/Regression Harness für ausgewählte Outputs (Analytics Metrics, Realized Equity Curve).

# Contracts
#   create_snapshot(target: str) -> dict : Erzeugt Datenstruktur für target
#   save_baseline(target: str, snapshot: dict) -> Path
#   load_baseline(target: str) -> dict | None
#   diff_snapshot(target: str, current: dict, baseline: dict) -> list[DiffEntry]
#   ensure_and_diff(target: str, update: bool=False) -> SnapshotResult
#       - Wenn keine Baseline existiert -> legt Baseline an (status='baseline_created').
#       - Wenn Baseline existiert und keine Unterschiede -> status='no_diff'.
#       - Wenn Unterschiede -> status='diff'; update=True überschreibt Baseline (status='updated').

# Invariants
#   - Deterministische Eingaben (sample trades) – keine externe I/O außer Baseline-Datei
#   - Baseline Ablage: data/devtools/snapshots/<target>.json
#   - Format: {"target":..., "data":{...}, "schema_version":1}

# Dependencies
#   Internal: trade_repo, trade_model, analytics.metrics
#   External: stdlib only

# Tests
#   tests/test_snapshots.py (Baseline create, no diff, diff detection + update)

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from typing import List, Dict, Any
from .trade_repo import TradeRepository
from .trade_model import validate_trade_dict
from ..analytics.metrics import aggregate_metrics, realized_equity_curve

SCHEMA_VERSION = 1


def _sample_repo() -> TradeRepository:
    repo = TradeRepository()
    data = [
        {"trade_id":"b1","ts":"2024-01-01T10:00:00","ticker":"XYZ","action":"BUY","shares":5,"price":10,"fees":0},
        {"trade_id":"b2","ts":"2024-01-02T10:00:00","ticker":"XYZ","action":"BUY","shares":3,"price":11,"fees":0},
        {"trade_id":"s1","ts":"2024-01-03T10:00:00","ticker":"XYZ","action":"SELL","shares":4,"price":14,"fees":1},
    ]
    for r in data:
        repo.add_trade(validate_trade_dict(r))
    return repo


def create_snapshot(target: str) -> Dict[str, Any]:
    repo = _sample_repo()
    if target == "metrics":
        data = aggregate_metrics(repo.all())
    elif target == "equity_curve":
        curve = realized_equity_curve(repo.all())
        data = {"points": [(ts.isoformat(), v) for ts, v in curve]}
    else:
        raise ValueError(f"Unknown snapshot target: {target}")
    return {"target": target, "data": data, "schema_version": SCHEMA_VERSION}


def _snapshot_path(target: str) -> Path:
    base = Path("data/devtools/snapshots")
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{target}.json"


def save_baseline(target: str, snapshot: Dict[str, Any]) -> Path:
    p = _snapshot_path(target)
    p.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return p


def load_baseline(target: str) -> Dict[str, Any] | None:
    p = _snapshot_path(target)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


@dataclass
class DiffEntry:
    path: str
    baseline: Any
    current: Any


def _diff_dict(baseline: Any, current: Any, path: str = "") -> List[DiffEntry]:
    diffs: List[DiffEntry] = []
    if isinstance(baseline, dict) and isinstance(current, dict):
        keys = set(baseline.keys()) | set(current.keys())
        for k in sorted(keys):
            new_path = f"{path}.{k}" if path else k
            if k not in baseline:
                diffs.append(DiffEntry(new_path, None, current[k]))
            elif k not in current:
                diffs.append(DiffEntry(new_path, baseline[k], None))
            else:
                diffs.extend(_diff_dict(baseline[k], current[k], new_path))
    elif isinstance(baseline, list) and isinstance(current, list):
        if baseline != current:
            diffs.append(DiffEntry(path, baseline, current))
    else:
        if baseline != current:
            diffs.append(DiffEntry(path, baseline, current))
    return diffs


@dataclass
class SnapshotResult:
    status: str  # baseline_created|no_diff|diff|updated
    target: str
    diff: List[Dict[str, Any]] | None
    snapshot: Dict[str, Any]

    def to_dict(self) -> dict:
        return {"status": self.status, "target": self.target, "diff": self.diff, "snapshot": self.snapshot}


def ensure_and_diff(target: str, update: bool = False) -> SnapshotResult:
    current = create_snapshot(target)
    baseline = load_baseline(target)
    if baseline is None:
        save_baseline(target, current)
        return SnapshotResult(status="baseline_created", target=target, diff=None, snapshot=current)
    diffs = _diff_dict(baseline.get("data"), current.get("data"))
    if not diffs:
        return SnapshotResult(status="no_diff", target=target, diff=None, snapshot=current)
    if update:
        save_baseline(target, current)
        return SnapshotResult(status="updated", target=target, diff=[asdict(d) for d in diffs], snapshot=current)
    return SnapshotResult(status="diff", target=target, diff=[asdict(d) for d in diffs], snapshot=current)
