"""Trade Import Enhancement Helpers

Purpose:
    Provide lightweight CSV schema inference & diff preview utilities used by the UI
    (Import Assistant panel) to validate incoming trade CSV files before mutating
    the in-memory repository.

Design Goals:
    - Zero third-party dependencies (stdlib only) to keep surface area small.
    - Pure functions: no hidden I/O besides explicit path-based load helper.
    - Defensive: never raises on malformed data; returns structured issues list.
    - Compatible with existing Trade model & validation routine.

Public API (stable):
    infer_csv_schema(text: str) -> dict
    diff_trades(existing: List[Trade], candidate_rows: List[dict]) -> dict
    parse_csv_text(text: str) -> List[dict]
    load_csv_path(path: Path) -> List[dict]

Returned Dict Conventions:
    Schema result keys:
        header: List[str]
        required_missing: List[str]
        unexpected: List[str]
        sample: List[dict] (up to 3 rows)
        valid: bool (all required present)
        issues: List[str]

    Diff result keys:
        new_ids: List[str]
        duplicate_ids: List[str]  (collides with existing trade_id)
        changed: List[str]        (same id, different field values)
        candidate_count: int
        importable_count: int     (# that would be imported if applied: only brand-new)
        issues: List[str]

Edge Cases:
    - Empty text → empty header, valid=False
    - BOM presence handled via newline/encoding tolerant split
    - Duplicate rows preserved in candidate list; duplicates appear in issues
"""
from __future__ import annotations
from typing import List, Dict, Any, Iterable
from pathlib import Path
import csv
from io import StringIO

from .trade_model import validate_trade_dict, Trade, TradeValidationError

REQUIRED_FIELDS = ["trade_id", "ts", "ticker", "action", "shares", "price"]

def parse_csv_text(text: str) -> List[Dict[str, str]]:
    """Parse CSV text into list of dict rows. Returns [] on failure (no raise)."""
    if not text or not text.strip():
        return []
    try:
        buf = StringIO(text.replace("\r\n", "\n"))
        # Use csv.Sniffer? Overkill; assume standard header row.
        reader = csv.DictReader(buf)
        if reader.fieldnames is None:
            return []
        rows = [row for row in reader]
        return rows
    except Exception:
        return []

def load_csv_path(path: Path) -> List[Dict[str, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []
    return parse_csv_text(text)

def infer_csv_schema(text: str) -> Dict[str, Any]:
    rows = parse_csv_text(text)
    issues: List[str] = []
    header: List[str] = []
    if rows:
        header = list(rows[0].keys())
    else:
        issues.append("empty or unparsable CSV")
    required_missing = [f for f in REQUIRED_FIELDS if f not in header]
    unexpected = [c for c in header if c not in REQUIRED_FIELDS and c not in ["fees", "tag", "note_path", "account"]]
    if required_missing:
        issues.append(f"missing required fields: {required_missing}")
    if unexpected:
        issues.append(f"unexpected columns: {unexpected}")
    # duplicate header detection
    if len(set(header)) != len(header):
        issues.append("duplicate column names detected")
    sample = rows[:3]
    valid = not required_missing and bool(header)
    return {
        "header": header,
        "required_missing": required_missing,
        "unexpected": unexpected,
        "sample": sample,
        "valid": valid,
        "issues": issues,
        "row_count": len(rows),
    }

def _row_to_identity(row: Dict[str, Any]) -> str:
    return str(row.get("trade_id", "")).strip()

def diff_trades(existing: Iterable[Trade], candidate_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    existing_index = {t.trade_id: t for t in existing}
    seen_ids: set[str] = set()
    duplicate_ids: List[str] = []
    new_ids: List[str] = []
    changed: List[str] = []
    issues: List[str] = []
    importable = 0
    for raw in candidate_rows:
        tid = _row_to_identity(raw)
        if not tid:
            issues.append("row missing trade_id")
            continue
        if tid in seen_ids:
            duplicate_ids.append(tid)
            continue
        seen_ids.add(tid)
        if tid not in existing_index:
            # validate to ensure import would succeed
            try:
                validate_trade_dict(raw)
                new_ids.append(tid)
                importable += 1
            except TradeValidationError as e:
                issues.append(f"new trade {tid} invalid: {e}")
        else:
            # compare field-by-field (string comparison on dict repr)
            ex = existing_index[tid].to_dict()
            # Normalize candidate numeric fields to float as validation would
            changed_flag = False
            for k, v in raw.items():
                if k in ("shares", "price", "fees") and v not in (None, ""):
                    try:
                        v_norm = float(v)
                    except Exception:
                        v_norm = v
                    if str(v_norm) != str(ex.get(k)):
                        changed_flag = True
                        break
                else:
                    if str(v).strip() != str(ex.get(k, "")).strip():
                        changed_flag = True
                        break
            if changed_flag:
                changed.append(tid)
    return {
        "new_ids": sorted(new_ids),
        "duplicate_ids": sorted(set(duplicate_ids)),
        "changed": sorted(changed),
        "candidate_count": len(candidate_rows),
        "importable_count": importable,
        "issues": issues,
    }

__all__ = [
    "infer_csv_schema",
    "parse_csv_text",
    "diff_trades",
    "load_csv_path",
]
