"""Deprecated shim after migration to `app.internal.admin_devtools`.

Investor UI removed DevTools panels; this module remains only to avoid breaking existing imports.
Will be removed in a future cleanup release.
"""
from __future__ import annotations
from app.internal.admin_devtools import *  # type: ignore F401,F403

__all__ = [
    'run_tests','run_lint_report','list_benchmarks','list_snapshot_targets','run_snapshot',
    'run_test_center','test_center_flag_enabled','submit_test_run','list_test_runs','get_test_run','get_test_run_output','retry_test_run',
    'parse_coverage_xml_safe','parse_junit_xml_safe','summarize_test_center_runs','artifact_file_readable'
]


def get_test_center_artifacts() -> dict | None:  # deprecated no-op
    return None


def list_test_center_runs(limit: int = 10) -> list[dict]:  # deprecated no-op
    return []


def get_test_center_run(run_id: str) -> dict:  # deprecated always raises
    raise ValueError("test center UI removed")


# --- Increment I1 Helpers (UI-safe, streamlit-frei testbar) ---
def test_center_flag_enabled() -> bool:
    """Return True if Test Center Panel should be visible (env flag VEK_TEST_CENTER=1). Default off."""
    import os
    return bool(int(os.environ.get("VEK_TEST_CENTER", "0")))


def test_center_latest_summary_exists() -> bool:  # deprecated always False
    return False


# --- Increment I2: Coverage / JUnit parsing + summarization (additive, streamlit-frei) ---
def parse_coverage_xml_safe(path: str | None) -> dict:
    """Parse minimal coverage percent from a coverage.xml (pytest-cov) file.
    Returns {'coverage_pct': float|None}. Never raises; invalid/missing -> None.
    """
    if not path:
        return {"coverage_pct": None}
    try:
        from xml.etree import ElementTree as ET
        import os
        if not os.path.exists(path):
            return {"coverage_pct": None}
        tree = ET.parse(path)
        root = tree.getroot()
        # pytest-cov xml root tag is <coverage line-rate="0.85" ...>
        line_rate = root.get("line-rate")
        if line_rate is None:
            return {"coverage_pct": None}
        try:
            pct = round(float(line_rate) * 100, 2)
        except Exception:
            pct = None
        return {"coverage_pct": pct}
    except Exception:
        return {"coverage_pct": None}


def parse_junit_xml_safe(path: str | None) -> dict:
    """Parse minimal JUnit summary: tests, failures, errors from junit.xml.
    Returns {'tests': int|None,'failures':int|None,'errors':int|None}. Never raises.
    """
    if not path:
        return {"tests": None, "failures": None, "errors": None}
    try:
        from xml.etree import ElementTree as ET
        import os
        if not os.path.exists(path):
            return {"tests": None, "failures": None, "errors": None}
        tree = ET.parse(path)
        root = tree.getroot()
        # Root could be <testsuite> or <testsuites>
        if root.tag == "testsuite":
            tests = root.get("tests")
            failures = root.get("failures")
            errors = root.get("errors")
        else:
            # aggregate testsuites children
            tests = failures = errors = 0
            found = False
            for ts in root.findall("testsuite"):
                found = True
                try:
                    tests += int(ts.get("tests", 0))
                    failures += int(ts.get("failures", 0))
                    errors += int(ts.get("errors", 0))
                except Exception:
                    pass
            if not found:
                tests = failures = errors = None
        def _toi(x):
            try:
                return int(x) if x is not None else None
            except Exception:
                return None
        return {"tests": _toi(tests), "failures": _toi(failures), "errors": _toi(errors)}
    except Exception:
        return {"tests": None, "failures": None, "errors": None}


def artifact_file_readable(path: str | None, size_limit: int = 200_000) -> bool:
    """Return True if artifact file exists & below size limit (for safe on-demand download)."""
    if not path:
        return False
    try:
        import os
        return os.path.exists(path) and os.path.getsize(path) <= size_limit
    except Exception:
        return False


def summarize_test_center_runs(limit: int = 5) -> list[dict]:
    """Return recent runs with parsed coverage/junit summary fields added.
    Each item extended with coverage_pct, junit_tests, junit_failures, junit_errors.
    """
    runs = list_test_center_runs(limit=limit)
    out: list[dict] = []
    for r in runs:
        arts = r.get("artifacts") or {}
        cov = parse_coverage_xml_safe(arts.get("coverage"))
        ju = parse_junit_xml_safe(arts.get("junit"))
        enriched = dict(r)
        enriched["coverage_pct"] = cov.get("coverage_pct")
        enriched["junit_tests"] = ju.get("tests")
        enriched["junit_failures"] = ju.get("failures")
        enriched["junit_errors"] = ju.get("errors")
        out.append(enriched)
    return out
