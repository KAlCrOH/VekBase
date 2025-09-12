"""
# ============================================================
# Context Banner — testqueue | Category: core
# Purpose: Lightweight in-process Test-Run Queue & Status Tracker für Admin/Investor Dev-Tools UI.

# Contracts
#   submit_run(k_expr:str|None, module_substr:str|None, nodeids:list[str]|None) -> str (run_id)
#   get_status(run_id:str) -> dict(status,passed,failed,stdout,stderr,queued_at,started_at,finished_at)
#   list_runs(limit:int=20) -> list[dict]
#   run_immediate(k_expr|module_substr|nodeids) -> dict  (Convenience: synchroner Aufruf bypass queue)
#
# Status Lifecycle
#   queued -> running -> (passed|failed|error)
#     error: spawn/timeout Fehler
#
# Invariants
#   - Single-threaded (kein paralleler Worker); Ausführung erfolgt beim Poll über process_next().
#   - Keine externen Nebenwirkungen außer pytest Subprocess.
#   - Deterministisch für gleiche Queue-Reihenfolge.
#
# Dependencies
#   Internal: app.core.devtools
#   External: stdlib
#
# Tests
#   tests/test_testqueue.py (added in increment)
#
# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Literal, Iterable
import time, uuid, threading, os, json, atexit, pathlib
from app.core import devtools as _dev


RunState = Literal["queued","running","passed","failed","error"]


@dataclass
class _QueuedRun:
    run_id: str
    k_expr: Optional[str]
    module_substr: Optional[str]
    nodeids: Optional[List[str]]
    status: RunState
    queued_at: float
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    passed: int = 0
    failed: int = 0
    stdout: str = ""
    stderr: str = ""
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    duration_s: float | None = None
    output_saved: bool = False

    def to_dict(self) -> Dict:
        d = asdict(self)
        return d


_QUEUE: List[_QueuedRun] = []
_HISTORY: List[_QueuedRun] = []  # finished runs (append order)
_LOCK = threading.Lock()
_WORKERS: List[threading.Thread] = []
_STOP = False

# Persistence (append-only JSONL + full outputs directory)
_BASE_DIR = os.path.join("data", "devtools")
_PERSIST_PATH = os.path.join(_BASE_DIR, "testqueue_runs.jsonl")
_OUTPUT_DIR = os.path.join(_BASE_DIR, "testqueue_outputs")
os.makedirs(_OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(_PERSIST_PATH), exist_ok=True)


def _persist_run(run: _QueuedRun):
    try:
        with open(_PERSIST_PATH, "a", encoding="utf-8") as f:
            json.dump(run.to_dict(), f, ensure_ascii=False)
            f.write("\n")
    except Exception:
        # Persistence best-effort; ignore errors
        pass


def _load_persisted(limit: int) -> List[Dict]:
    if not os.path.exists(_PERSIST_PATH):
        return []
    rows: List[Dict] = []
    try:
        with open(_PERSIST_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
    except Exception:
        return []
    return rows[-limit:]


def submit_run(k_expr: Optional[str] = None, module_substr: Optional[str] = None, nodeids: Optional[List[str]] = None) -> str:
    run = _QueuedRun(run_id=uuid.uuid4().hex[:10], k_expr=k_expr, module_substr=module_substr, nodeids=nodeids, status="queued", queued_at=time.time())
    with _LOCK:
        _QUEUE.append(run)
    return run.run_id


def _execute(run: _QueuedRun):
    run.started_at = time.time()
    run.status = "running"
    res = _dev.run_tests(nodeids=run.nodeids, k_expr=run.k_expr, module_substr=run.module_substr, timeout=180)
    full_stdout = res.stdout
    full_stderr = res.stderr
    summary = _dev.parse_summary(full_stdout)
    run.passed = summary["passed"]
    run.failed = summary["failed"]
    # Truncation
    max_len = int(os.environ.get("VEK_TESTQUEUE_MAX_OUTPUT", "4000"))
    def _truncate(txt: str):
        if len(txt) > max_len:
            return txt[:max_len] + f"\n... <truncated {len(txt)-max_len} chars>" , True
        return txt, False
    run.stdout, run.stdout_truncated = _truncate(full_stdout)
    run.stderr, run.stderr_truncated = _truncate(full_stderr)
    if run.stdout_truncated or run.stderr_truncated:
        try:
            base = pathlib.Path(_OUTPUT_DIR)
            (base / f"{run.run_id}_stdout.out").write_text(full_stdout, encoding="utf-8", errors="ignore")
            (base / f"{run.run_id}_stderr.out").write_text(full_stderr, encoding="utf-8", errors="ignore")
            run.output_saved = True
        except Exception:
            run.output_saved = False
    run.status = res.status  # passed/failed/error mapping deckungsgleich
    run.finished_at = time.time()
    if run.started_at:
        run.duration_s = round(run.finished_at - run.started_at, 4)


def process_next():
    """Process next queued run (synchronous single-run helper). Still used in legacy poll mode.
    Returns processed run_id or None.
    """
    with _LOCK:
        run = next((r for r in _QUEUE if r.status == "queued" and not r.started_at), None)
    if not run:
        return None
    try:
        _execute(run)
    except Exception as e:
        run.status = "error"
        run.stderr = str(e)
        run.finished_at = time.time()
    if run.finished_at:
        with _LOCK:
            _HISTORY.append(run)
            if len(_HISTORY) > 200:
                del _HISTORY[:-200]
        _persist_run(run)
    return run.run_id


def _worker_loop():
    while not _STOP:
        processed = process_next()
        if not processed:
            time.sleep(0.5)


def ensure_workers():
    """Spawn worker threads up to VEK_TESTQUEUE_WORKERS (default 0 = disabled). Idempotent."""
    target_count = int(os.environ.get("VEK_TESTQUEUE_WORKERS", "0"))
    if target_count <= 0:
        return 0
    with _LOCK:
        current = len(_WORKERS)
        while len(_WORKERS) < target_count:
            t = threading.Thread(target=_worker_loop, name=f"testqueue-worker-{len(_WORKERS)+1}", daemon=True)
            _WORKERS.append(t)
            t.start()
        return len(_WORKERS)


def shutdown_workers():
    global _STOP
    _STOP = True
    # join non-daemon threads if we ever make them non-daemon


atexit.register(shutdown_workers)


def get_status(run_id: str) -> Optional[Dict]:
    with _LOCK:
        for r in _QUEUE:
            if r.run_id == run_id:
                return r.to_dict()
        for r in _HISTORY:
            if r.run_id == run_id:
                return r.to_dict()
    return None


def list_runs(limit: int = 20, status: Optional[Iterable[str]] = None, include_persisted: bool = True) -> List[Dict]:
    """Return active + recent finished runs.
    Args:
      limit: total rows returned (history truncation after filtering)
      status: optional iterable of status strings to filter
      include_persisted: wenn True -> ergänzt aus JSONL Persistenz (nur finished)
    """
    status_set = set([s.strip() for s in status]) if status else None
    with _LOCK:
        active = [r.to_dict() for r in _QUEUE if r.status in ("queued","running")]
        hist = [r.to_dict() for r in _HISTORY]
    persisted: List[Dict] = []
    if include_persisted:
        persisted = _load_persisted(limit * 2)
    combined = active + hist[::-1] + [r for r in persisted[::-1] if not any(h["run_id"] == r.get("run_id") for h in hist)]
    if status_set:
        combined = [r for r in combined if r.get("status") in status_set]
    # Deduplicate by run_id keeping first occurrence (active > history > persisted order)
    seen = set()
    deduped: List[Dict] = []
    for r in combined:
        rid = r.get("run_id")
        if rid in seen:
            continue
        seen.add(rid)
        deduped.append(r)
    return deduped[:limit]


def run_immediate(k_expr: Optional[str] = None, module_substr: Optional[str] = None, nodeids: Optional[List[str]] = None) -> Dict:
    run_id = submit_run(k_expr=k_expr, module_substr=module_substr, nodeids=nodeids)
    process_next()  # will start & finish synchronously (since single run)
    return get_status(run_id) or {"error": "run not found"}


def retry_run(run_id: str) -> str | None:
    st = get_status(run_id)
    if not st:
        return None
    return submit_run(k_expr=st.get("k_expr"), module_substr=st.get("module_substr"), nodeids=st.get("nodeids"))


__all__ = [
    "submit_run","get_status","list_runs","process_next","run_immediate","ensure_workers","shutdown_workers","get_full_output","retry_run"
]

# Auto-start workers if configured
ensure_workers()


def get_full_output(run_id: str) -> Dict[str,str] | None:
    st = get_status(run_id)
    if not st:
        return None
    base = pathlib.Path(_OUTPUT_DIR)
    stdout_path = base / f"{run_id}_stdout.out"
    stderr_path = base / f"{run_id}_stderr.out"
    full_stdout = stdout_path.read_text(encoding="utf-8", errors="ignore") if stdout_path.exists() else st.get("stdout")
    full_stderr = stderr_path.read_text(encoding="utf-8", errors="ignore") if stderr_path.exists() else st.get("stderr")
    return {
        "run_id": run_id,
        "stdout": full_stdout,
        "stderr": full_stderr,
        "truncated_stdout": st.get("stdout_truncated", False),
        "truncated_stderr": st.get("stderr_truncated", False),
        "note": "complete" if not (st.get("stdout_truncated") or st.get("stderr_truncated")) else ("full output recovered from file" if (stdout_path.exists() or stderr_path.exists()) else "truncated (raw file missing)"),
    }
