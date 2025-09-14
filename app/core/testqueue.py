"""
# ============================================================
# Context Banner — testqueue | Category: core
# Purpose: In‑process (optional parallel) Test-Run Queue mit Persistenz & Audit Trail für DevTools UIs.

# Contracts
#   submit_run(k_expr|module_substr|nodeids) -> run_id(str)
#   get_status(run_id) -> dict(status, passed, failed, stdout, stderr, *_timestamps, truncation flags, duration_s)
#   list_runs(limit, status?, include_persisted: bool=True) -> List[dict]
#   process_next() -> run_id|None (Legacy Poll Mode)
#   ensure_workers() -> int (spawn worker threads gemäß Env `VEK_TESTQUEUE_WORKERS`)
#   get_full_output(run_id) -> vollständige stdout/stderr (rekonstruiert aus Persistenz falls truncation)
#   retry_run(run_id) -> new_run_id|None

# Status Lifecycle
#   queued -> running -> passed | failed | error
#   (error = interner Ausführungsfehler / Spawn / Timeout / unerwartete Exception)

# Invariants
#   - Parallelität über Worker Threads (0 = deaktiviert → Poll-Modus) steuerbar via Env `VEK_TESTQUEUE_WORKERS`.
#   - Append-only Persistenz: JSONL (`data/devtools/testqueue_runs.jsonl`) + vollständige Outputs (`data/devtools/testqueue_outputs/`).
#   - Truncation von stdout/stderr via Env `VEK_TESTQUEUE_MAX_OUTPUT` (Default 4000) mit Flag + optionaler vollständiger Dateipersistenz.
#   - Keine Netzwerkzugriffe; ausschließlich lokaler pytest Subprocess.
#   - Deterministische Reihenfolge FIFO für queued Runs.

# Dependencies
#   Internal: app.core.devtools (Run/Parse), stdlib (threading, json, atexit)
#   External: keine weiteren.

# Tests
#   tests/test_testqueue*.py (Basis, Parallel, Truncation, Retry/Full Output)

# Side-Effects
#   Writes: data/devtools/testqueue_runs.jsonl; data/devtools/testqueue_outputs/*.out

# Do-Not-Change
#   Banner policy-relevant (Änderungen nur via „Header aktualisieren“ Task)
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

# Persistence error tracking (debt item resolution)
_PERSIST_ERRORS_TOTAL = 0
_PERSIST_LAST_ERROR: str | None = None
_PERSIST_LAST_TS: float | None = None


def _apply_retention():
    """Retention Policy (Increment: queue retention).
    Controlled via env vars:
      VEK_TESTQUEUE_MAX_RUNS (int>0) -> keep at most this many finished runs in JSONL (truncate oldest lines)
      VEK_TESTQUEUE_MAX_BYTES (int>0) -> best-effort cap for outputs directory total size (delete oldest *_stdout.out/_stderr.out pairs)
    Silent failures avoided: exceptions propagated only as return (ignored by caller) to keep queue running.
    """
    max_runs_raw = os.environ.get("VEK_TESTQUEUE_MAX_RUNS")
    max_bytes_raw = os.environ.get("VEK_TESTQUEUE_MAX_BYTES")
    try:
        max_runs = int(max_runs_raw) if max_runs_raw else None
        if max_runs is not None and max_runs <= 0:
            max_runs = None
    except Exception:
        max_runs = None
    try:
        max_bytes = int(max_bytes_raw) if max_bytes_raw else None
        if max_bytes is not None and max_bytes <= 0:
            max_bytes = None
    except Exception:
        max_bytes = None
    # Truncate JSONL by lines
    if max_runs and os.path.exists(_PERSIST_PATH):
        try:
            with open(_PERSIST_PATH, "r", encoding="utf-8") as f:
                lines = [ln for ln in f.readlines() if ln.strip()]
            if len(lines) > max_runs:
                # Keep most recent max_runs (end of file are newest by append semantics)
                kept = lines[-max_runs:]
                with open(_PERSIST_PATH, "w", encoding="utf-8") as fw:
                    fw.writelines([ln if ln.endswith("\n") else ln+"\n" for ln in kept])
        except Exception:
            # Best-effort; do not raise (queue not critical infra)
            pass
    # Cap outputs directory size
    if max_bytes:
        try:
            files = []
            for p in pathlib.Path(_OUTPUT_DIR).glob("*_stdout.out"):
                stem = p.name[:-11]  # remove _stdout.out
                stderr_path = p.parent / f"{stem}_stderr.out"
                size = p.stat().st_size + (stderr_path.stat().st_size if stderr_path.exists() else 0)
                mtime = p.stat().st_mtime
                files.append((mtime, size, stem, p, stderr_path))
            total = sum(f[1] for f in files)
            if total > max_bytes:
                # delete oldest until under threshold
                for mtime, size, stem, p_stdout, p_stderr in sorted(files, key=lambda x: x[0]):
                    try:
                        if p_stdout.exists():
                            p_stdout.unlink()
                        if p_stderr.exists():
                            p_stderr.unlink()
                    except Exception:
                        pass
                    total -= size
                    if total <= max_bytes:
                        break
        except Exception:
            pass


def _persist_run(run: _QueuedRun):
    global _PERSIST_ERRORS_TOTAL, _PERSIST_LAST_ERROR, _PERSIST_LAST_TS
    try:
        with open(_PERSIST_PATH, "a", encoding="utf-8") as f:
            json.dump(run.to_dict(), f, ensure_ascii=False)
            f.write("\n")
        _apply_retention()  # enforce after each append
    except Exception as e:
        # Record error statistics instead of silent pass
        _PERSIST_ERRORS_TOTAL += 1
        _PERSIST_LAST_ERROR = str(e)[:500]
        _PERSIST_LAST_TS = time.time()

def get_persistence_stats() -> Dict[str, object]:
    """Return counters for persistence layer health."""
    return {
        "errors_total": _PERSIST_ERRORS_TOTAL,
        "last_error": _PERSIST_LAST_ERROR,
        "last_error_ts": _PERSIST_LAST_TS,
        "persist_path": _PERSIST_PATH,
    }


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
    "submit_run","get_status","list_runs","process_next","run_immediate","ensure_workers","shutdown_workers","get_full_output","retry_run","aggregate_metrics","get_persistence_stats","_reset_state_for_tests"
]

# --- Aggregation (Increment: queue aggregate metrics) ---
def aggregate_metrics(limit: int = 100) -> Dict[str, float | int | str | None]:
    """Compute simple aggregate metrics over recent finished runs (in-memory only).
    Args:
      limit: number of most recent finished runs from _HISTORY (tail) to include.
    Returns dict with counts and rates; empty values when no finished runs.
    Notes:
      - Uses only in-process state (keine JSONL Re-Reads) to stay lightweight/auditierbar.
      - Rates are 0.0 when denominator = 0.
    """
    with _LOCK:
        finished = [r for r in _HISTORY][-limit:]
    total = len(finished)
    if total == 0:
        return {
            "total_runs": 0,
            "mean_duration_s": None,
            "median_duration_s": None,
            "p95_duration_s": None,
            "pass_rate": 0.0,
            "fail_rate": 0.0,
            "error_rate": 0.0,
            "last_run_id": "",
        }
    passed = sum(1 for r in finished if r.status == "passed")
    failed = sum(1 for r in finished if r.status == "failed")
    errored = sum(1 for r in finished if r.status == "error")
    durations = [r.duration_s for r in finished if isinstance(r.duration_s, (int,float))]
    mean_dur = round(sum(durations)/len(durations), 4) if durations else None
    last_id = finished[-1].run_id if finished else ""
    denom = float(total) if total else 1.0
    # median & p95 helper
    def _median(vals: List[float]) -> float | None:
        if not vals:
            return None
        s = sorted(vals)
        n = len(s)
        mid = n // 2
        if n % 2 == 1:
            return s[mid]
        return (s[mid-1] + s[mid]) / 2.0
    def _p95(vals: List[float]) -> float | None:
        if not vals:
            return None
        s = sorted(vals)
        idx = int(0.95 * (len(s)-1))
        return s[idx]
    median_dur = _median(durations)
    p95_dur = _p95(durations)
    return {
        "total_runs": total,
        "mean_duration_s": mean_dur,
        "median_duration_s": median_dur,
        "p95_duration_s": p95_dur,
        "pass_rate": round(passed/denom, 4),
        "fail_rate": round(failed/denom, 4),
        "error_rate": round(errored/denom, 4),
        "last_run_id": last_id,
    }

# --- Test Support (Isolation) ---
def _reset_state_for_tests():
    """Clear in-memory queue/history for test isolation.
    Does NOT touch persisted JSONL or outputs to avoid destructive side-effects.
    Intended for use only inside unit tests where cross-test contamination occurs.
    """
    with _LOCK:
        _QUEUE.clear()
        _HISTORY.clear()

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
