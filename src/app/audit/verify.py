from __future__ import annotations
from pathlib import Path
import pyarrow.parquet as pq
import hashlib
from typing import Dict, Any

# Placeholder: once prompt_hash/completion_hash stored we recompute.

def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_bundle(path: Path) -> Dict[str, Any]:
    table = pq.read_table(path)
    if table.num_rows != 1:
        raise ValueError("Bundle parquet must contain exactly one row")
    row = table.to_pylist()[0]
    return row


def verify_bundle(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"status": "error", "error": "not_found"}
    try:
        row = load_bundle(p)
        # Planned fields: prompt_filled, completion, prompt_hash, completion_hash
        prompt = row.get("prompt")
        completion = row.get("completion")
        # If hash fields present, verify, else mark pending
        prompt_hash_stored = row.get("prompt_hash")
        completion_hash_stored = row.get("completion_hash")
        results = {}
        if prompt_hash_stored and isinstance(prompt, list):
            # Convert structured prompt to flat string for hashing attempt
            flat = "\n".join([seg.get("text", "") for seg in prompt if isinstance(seg, dict)])
            computed = sha256_str(flat)
            results["prompt_hash_match"] = computed == prompt_hash_stored
            results["prompt_hash_computed"] = computed
        else:
            results["prompt_hash_match"] = None
        if completion_hash_stored and isinstance(completion, str):
            computed_c = sha256_str(completion)
            results["completion_hash_match"] = computed_c == completion_hash_stored
            results["completion_hash_computed"] = computed_c
        else:
            results["completion_hash_match"] = None
        return {"status": "ok", "bundle_path": str(p), **results}
    except Exception as e:
        return {"status": "error", "error": str(e)}
