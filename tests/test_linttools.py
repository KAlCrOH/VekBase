"""
# ============================================================
# Context Banner — test_linttools | Category: test
# Purpose: Verifiziert leichte Lint-Prüfungen (Syntax + Whitespace + Mixed Indent)

# Contracts
#   Inputs: temporäre Testdateien / bestehende Module
#   Outputs: Assertions auf LintReport Struktur
#   Determinism: Deterministisch

# Invariants
#   - Syntaxfehler -> mindestens 1 error Issue
#   - Saubere Datei -> keine error Issues

# Dependencies
#   Internal: app.core.linttools
#   External: stdlib (tempfile, pathlib)

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from app.core.linttools import run_lint
from pathlib import Path
import tempfile


def test_run_lint_clean_subset():
    # Use a known good file (metrics module) and expect zero syntax errors
    report = run_lint(["app/analytics/metrics.py"])  # narrow scope
    error_codes = [i.code for i in report.issues if i.severity == "error"]
    assert "SYNTAX_ERROR" not in error_codes


def test_run_lint_with_syntax_error():
    with tempfile.TemporaryDirectory() as tmp:
        bad_file = Path(tmp) / "bad_sample.py"
        bad_file.write_text("def broken(:\n    pass\n", encoding="utf-8")
        report = run_lint([str(tmp)])
        assert report.error_count >= 1
        assert any(i.code == "SYNTAX_ERROR" for i in report.issues)
