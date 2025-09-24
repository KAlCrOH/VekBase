"""
# ============================================================
# Context Banner — devtools | Category: core
# Purpose: Test Discovery & Execution Abstraktion für UI (Konsole/Admin) — kapselt subprocess Aufrufe von pytest

# Contracts
#   Functions:
#     discover_tests(k_expr: str|None = None, module_substr: str|None = None, timeout=60) -> list[str]
#       - Gibt NodeIDs der gefundenen Tests zurück (leer = keine Treffer, kein Fehler)
#     run_tests(nodeids: list[str] | None = None, k_expr: str|None = None, module_substr: str|None = None, timeout=120) -> TestRunResult
#       - Führt Tests synchron aus (Subprozess) und liefert strukturiertes Ergebnis (stdout, stderr, returncode, status)
#   Side-Effects: subprocess spawn (pytest), keine Netzwerkaufrufe, keine versteckten Dateizugriffe außer pytest Standard.
#   Determinism: Deterministisch für gleiche Testbasis & Filter.

# Invariants
#   - Keine sys.path Hacks; nutzt sys.executable -m pytest
#   - UI konsumiert nur public API (discover_tests, run_tests, parse_summary)
#   - Keine globale Mutation außerhalb dieses Moduls

# Dependencies
#   Internal: none (nur von UI importiert)
#   External: stdlib (subprocess, sys, re, dataclasses, typing)

# Tests
#   tests/test_devtools.py (Discovery, Run Erfolg & Negativfall)

# Do-Not-Change
#   Banner policy-relevant; Änderungen nur via Task „Header aktualisieren“.
# ============================================================
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Literal, Optional
import subprocess, sys, re, os, time
from pathlib import Path

# Public export list (initialized early so later additive helpers can append)
__all__: list[str] = [
    'TestDiscoveryError', 'TestRunResult', 'discover_tests', 'run_tests', 'parse_summary'
]


class TestDiscoveryError(Exception):
    """Raised when discovery subprocess itself fails (nicht bei 0 Treffern)."""


@dataclass
class TestRunResult:
    status: Literal["passed", "failed", "error"]
    returncode: Optional[int]
    stdout: str
    stderr: str
    collected: List[str] | None = None


def _resolve_module_args(module_substr: str | None) -> List[str]:
    """Return list of path arguments to pass to pytest based on a substring or direct path.
    Behavior:
      - If module_substr is an existing path -> return [module_substr]
      - Else search under ./tests for files containing substring; return all matches (paths).
      - If no matches -> return [] (pytest will use default discovery when we supply no path args).
    This keeps UI ergonomic (substring) while avoiding discovery errors for common inputs like 'test_metrics'.
    """
    if not module_substr:
        return []
    if os.path.exists(module_substr):
        return [module_substr]
    matches: List[str] = []
    tests_root = Path("tests")
    if tests_root.exists():
        for p in tests_root.rglob("test_*.py"):
            if module_substr in p.name:
                matches.append(str(p))
    return matches


def discover_tests(k_expr: str | None = None, module_substr: str | None = None, timeout: int = 60) -> List[str]:
    """Discover test nodeids using pytest --collect-only.
    Returns list of nodeids (can be empty). Raises TestDiscoveryError if subprocess errors.
    Filtering:
      - k_expr -> passed to -k
      - module_substr -> appended as positional arg (substring / path fragment)
    """
    args = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    if k_expr:
        args.extend(["-k", k_expr])
    for mod_arg in _resolve_module_args(module_substr):
        args.append(mod_arg)
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except Exception as e:  # timeout oder spawn Fehler
        raise TestDiscoveryError(str(e)) from e
    if proc.returncode not in (0, 5):  # pytest returns 5 when no tests collected
        # treat other non-zero codes as discovery error
        raise TestDiscoveryError(proc.stderr or proc.stdout)
    lines = [ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip()]
    nodeids = [ln for ln in lines if not re.search(r"collected \d+ items", ln)]
    # Remove summary or blank artifacts
    nodeids = [nid for nid in nodeids if not nid.lower().startswith("warning:")]
    return nodeids


def run_tests(nodeids: List[str] | None = None, k_expr: str | None = None, module_substr: str | None = None, timeout: int = 120, maxfail: int | None = None) -> TestRunResult:
    """Run tests and return structured result.
    Precedence: explicit nodeids > k_expr/module filters.
    Status Mapping:
      returncode == 0 -> passed
      returncode > 0  -> failed
      Exception (timeout/spawn) -> error
    """
    args = [sys.executable, "-m", "pytest", "-q"]
    if maxfail is None:
        # allow override via env
        try:
            mf_env = os.environ.get("VEK_TEST_MAXFAIL")
            if mf_env:
                maxfail = int(mf_env)
        except Exception:
            maxfail = None
    if maxfail:
        args.extend(["--maxfail", str(maxfail)])
    if nodeids:
        args.extend(nodeids)
    else:
        if k_expr:
            args.extend(["-k", k_expr])
        for mod_arg in _resolve_module_args(module_substr):
            args.append(mod_arg)
    # Simple file lock to avoid concurrent heavy test runs (best-effort)
    lock_path = Path('.pytest_run.lock')
    lock_acquired = False
    lock_wait_start = time.time()
    lock_timeout = int(os.environ.get("VEK_TEST_LOCK_TIMEOUT", "30"))
    while not lock_acquired:
        try:
            # exclusive create
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            lock_acquired = True
        except FileExistsError:
            if time.time() - lock_wait_start > lock_timeout:
                # give up; proceed anyway
                break
            time.sleep(0.25)
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        rc = proc.returncode
        status: Literal["passed", "failed", "error"] = "passed" if rc == 0 else "failed"
        return TestRunResult(status=status, returncode=rc, stdout=proc.stdout or "", stderr=proc.stderr or "")
    except Exception as e:  # Timeout oder Prozessfehler
        return TestRunResult(status="error", returncode=None, stdout="", stderr=str(e))
    finally:
        if lock_acquired:
            try:
                lock_path.unlink(missing_ok=True)  # py>=3.8
            except Exception:
                pass


def parse_summary(stdout: str) -> dict:
    """Parse a minimal summary (counts) from pytest -q stdout.
    Heuristik: zählt Zeilen mit ::PASSED/FAILED/SKIPPED/ERROR.
    """
    passed = len([ln for ln in stdout.splitlines() if re.search(r"::(PASSED|SKIPPED)", ln)])
    failed = len([ln for ln in stdout.splitlines() if re.search(r"::(FAILED|ERROR)", ln)])
    return {"passed": passed, "failed": failed}


# ============================================================
# Additive Helpers (Increment I1 - Test Center) — artefaktbezogene Utilities
# Contracts (additiv, kein Breaking Change):
#   generate_run_id() -> str  (zeitbasierte eindeutige ID)
#   artifact_dir(run_id) -> Path (stellt sicher, dass Basisverzeichnis existiert)
#   run_tests_with_artifacts(k_expr|nodeids) -> (TestRunResult, dict(paths))
#
#   Artefakt-Layout:
#     .artifacts/tests/<run_id>/summary.json
#     .artifacts/tests/<run_id>/junit.xml
#     .artifacts/tests/<run_id>/coverage.xml  (xml) / lcov.info optional
#
#   Policy: keine externen Dependencies; reine stdlib.
#   Coverage/JUnit: via Pytest Plugins falls verfügbar; wir erzwingen Standardargumente --junitxml & --cov (wenn pytest-cov installiert; falls nicht, toleranter Fallback)
#   Netzwerk: none
# ============================================================
import json as _json, time as _time, uuid as _uuid

def generate_run_id() -> str:
    # Kombiniert Zeitpräfix für Sortierbarkeit + kurze UUID
    return f"{int(_time.time())}-{_uuid.uuid4().hex[:8]}"


def artifact_dir(run_id: str) -> Path:
    base = Path('.artifacts') / 'tests' / run_id
    base.mkdir(parents=True, exist_ok=True)
    return base


def _build_pytest_args_for_artifacts(run_id: str, nodeids: List[str] | None, k_expr: str | None, module_substr: str | None) -> List[str]:
    args = [sys.executable, '-m', 'pytest', '-q']
    # JUnit / Coverage: tolerant, auch wenn pytest-cov nicht installiert ist (Plugin ignoriert Parameter?)
    junit_path = artifact_dir(run_id) / 'junit.xml'
    coverage_path = artifact_dir(run_id) / 'coverage.xml'
    # Add standard artifact args
    args.extend(['--junitxml', str(junit_path)])
    # Coverage: falls plugin nicht vorhanden führt es zu Fehler -> daher guarded: wir aktivieren nur wenn pytest-cov via import verfügbar
    try:
        import importlib
        importlib.import_module('pytest_cov')  # noqa: F401
        # Standard: Branch + XML
        args.extend(['--cov=app', f'--cov-report=xml:{coverage_path}', '--cov-report=term'])
    except Exception:
        pass  # still run tests without coverage
    if nodeids:
        args.extend(nodeids)
    else:
        if k_expr:
            args.extend(['-k', k_expr])
        for mod_arg in _resolve_module_args(module_substr):
            args.append(mod_arg)
    return args


def run_tests_with_artifacts(nodeids: List[str] | None = None, k_expr: str | None = None, module_substr: str | None = None, timeout: int = 180) -> tuple[TestRunResult, dict]:
    """Run tests and persist junit/coverage + summary.json.
    Rückgabewert: (TestRunResult, artifact_info_dict)
    artifact_info_dict = { 'run_id': str, 'paths': { 'junit': str|None, 'coverage': str|None, 'summary': str } }
    Fehlerfall: läuft Tests trotzdem (ohne Coverage) und erstellt summary.
    """
    run_id = generate_run_id()
    args = _build_pytest_args_for_artifacts(run_id, nodeids=nodeids, k_expr=k_expr, module_substr=module_substr)
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        rc = proc.returncode
        status: Literal['passed','failed','error'] = 'passed' if rc == 0 else 'failed'
        result = TestRunResult(status=status, returncode=rc, stdout=proc.stdout or '', stderr=proc.stderr or '')
    except Exception as e:
        result = TestRunResult(status='error', returncode=None, stdout='', stderr=str(e))
    # Summary schreiben
    summary = parse_summary(result.stdout)
    art_dir = artifact_dir(run_id)
    summary_path = art_dir / 'summary.json'
    try:
        with summary_path.open('w', encoding='utf-8') as f:
            _json.dump({'run_id': run_id, 'status': result.status, 'passed': summary['passed'], 'failed': summary['failed']}, f, ensure_ascii=False, indent=2)
    except Exception:
        # Ignorieren – UI kann ohne summary leben
        pass
    junit_path = art_dir / 'junit.xml'
    cov_path = art_dir / 'coverage.xml'
    artifacts = {
        'run_id': run_id,
        'paths': {
            'junit': str(junit_path) if junit_path.exists() else None,
            'coverage': str(cov_path) if cov_path.exists() else None,
            'summary': str(summary_path) if summary_path.exists() else None,
        }
    }
    return result, artifacts


__all__ += [
    'generate_run_id','artifact_dir','run_tests_with_artifacts'
]
