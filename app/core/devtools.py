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
import subprocess, sys, re, os
from pathlib import Path


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


def run_tests(nodeids: List[str] | None = None, k_expr: str | None = None, module_substr: str | None = None, timeout: int = 120) -> TestRunResult:
    """Run tests and return structured result.
    Precedence: explicit nodeids > k_expr/module filters.
    Status Mapping:
      returncode == 0 -> passed
      returncode > 0  -> failed
      Exception (timeout/spawn) -> error
    """
    args = [sys.executable, "-m", "pytest", "-q"]
    if nodeids:
        args.extend(nodeids)
    else:
        if k_expr:
            args.extend(["-k", k_expr])
        for mod_arg in _resolve_module_args(module_substr):
            args.append(mod_arg)
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        rc = proc.returncode
        status: Literal["passed", "failed", "error"] = "passed" if rc == 0 else "failed"
        return TestRunResult(status=status, returncode=rc, stdout=proc.stdout or "", stderr=proc.stderr or "")
    except Exception as e:  # Timeout oder Prozessfehler
        return TestRunResult(status="error", returncode=None, stdout="", stderr=str(e))


def parse_summary(stdout: str) -> dict:
    """Parse a minimal summary (counts) from pytest -q stdout.
    Heuristik: zählt Zeilen mit ::PASSED/FAILED/SKIPPED/ERROR.
    """
    passed = len([ln for ln in stdout.splitlines() if re.search(r"::(PASSED|SKIPPED)", ln)])
    failed = len([ln for ln in stdout.splitlines() if re.search(r"::(FAILED|ERROR)", ln)])
    return {"passed": passed, "failed": failed}
