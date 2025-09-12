"""
# ============================================================
# Context Banner — linttools | Category: core
# Purpose: Lightweight lokale Lint-Prüfungen (Syntax & einfache Stilregeln) ohne externe Dependencies.

# Contracts
#   run_lint(paths: list[str] | None = None) -> LintReport
#       - Prüft Python-Dateien (UTF-8) auf:
#           * Syntaxfehler (compile)
#           * Trailing Whitespace
#           * Tab-Mix (Tab + Space gemischt in indent) — heuristisch
#       - paths: Wenn None -> durchsucht ./app und ./tests rekursiv
#   Data Classes: LintIssue (file, line, col, code, message, severity)
#                 LintReport (issues, stats)
#   Keine Netzwerkzugriffe; reiner Dateilesezugriff.

# Invariants
#   - Kein Schreiben von Dateien
#   - Stabiler Output (Determinismus)
#   - Erweiterbar für weitere Checks (Additiv)

# Dependencies
#   External: stdlib only

# Tests
#   tests/test_linttools.py (happy path + synthetischer Syntaxfehler)

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class LintIssue:
    file: str
    line: int
    col: int
    code: str  # e.g. SYNTAX_ERROR, TRAILING_WS, MIXED_INDENT
    message: str
    severity: str  # info|warning|error


@dataclass
class LintReport:
    issues: List[LintIssue]

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    def to_dict(self) -> dict:
        return {
            "issues": [i.__dict__ for i in self.issues],
            "errors": self.error_count,
            "warnings": self.warning_count,
            "total": len(self.issues),
        }


def _discover_py_files(paths: Optional[List[str]]) -> List[Path]:
    if paths:
        out: List[Path] = []
        for p in paths:
            path = Path(p)
            if path.is_file() and path.suffix == ".py":
                out.append(path)
            elif path.is_dir():
                out.extend([f for f in path.rglob("*.py")])
        return out
    base_dirs = [Path("app"), Path("tests")]
    files: List[Path] = []
    for d in base_dirs:
        if d.exists():
            files.extend([f for f in d.rglob("*.py")])
    return files


def run_lint(paths: Optional[List[str]] = None) -> LintReport:
    issues: List[LintIssue] = []
    for file in _discover_py_files(paths):
        try:
            text = file.read_text(encoding="utf-8")
        except Exception as e:
            issues.append(LintIssue(str(file), 0, 0, "IO_ERROR", f"Cannot read file: {e}", "error"))
            continue
        # Syntax check
        try:
            compile(text, str(file), 'exec')
        except SyntaxError as e:
            issues.append(LintIssue(str(file), e.lineno or 0, e.offset or 0, "SYNTAX_ERROR", e.msg, "error"))
        # Trailing whitespace & mixed indent
        for idx, line in enumerate(text.splitlines(), start=1):
            if line.rstrip() != line:
                issues.append(LintIssue(str(file), idx, len(line), "TRAILING_WS", "Trailing whitespace", "warning"))
            # Mixed indentation: leading segment contains both tabs and spaces
            leading = line[:len(line)-len(line.lstrip())]
            if '\t' in leading and ' ' in leading:
                issues.append(LintIssue(str(file), idx, 0, "MIXED_INDENT", "Mixed tabs/spaces indentation", "warning"))
    return LintReport(issues)
