"""
Tests for Increment I2: coverage/junit parsing & summarization helpers.
"""
from pathlib import Path
from app.ui import admin_devtools as adm_dt
import textwrap


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_parse_coverage_xml_safe_valid(tmp_path):
    xml = """<coverage line-rate='0.875' branch-rate='0.5'></coverage>"""
    p = _write(tmp_path, "coverage.xml", xml)
    out = adm_dt.parse_coverage_xml_safe(str(p))
    assert out["coverage_pct"] == 87.5


def test_parse_coverage_xml_safe_invalid(tmp_path):
    p = _write(tmp_path, "coverage.xml", "<notcov>")
    out = adm_dt.parse_coverage_xml_safe(str(p))
    assert out["coverage_pct"] is None


def test_parse_junit_xml_safe_single_suite(tmp_path):
    xml = textwrap.dedent("""
    <testsuite name='x' tests='5' failures='1' errors='0'>
    </testsuite>
    """)
    p = _write(tmp_path, "junit.xml", xml)
    out = adm_dt.parse_junit_xml_safe(str(p))
    assert out == {"tests":5,"failures":1,"errors":0}


def test_parse_junit_xml_safe_multi(tmp_path):
    xml = textwrap.dedent("""
    <testsuites>
      <testsuite name='a' tests='3' failures='0' errors='0'/>
      <testsuite name='b' tests='2' failures='1' errors='0'/>
    </testsuites>
    """)
    p = _write(tmp_path, "junit.xml", xml)
    out = adm_dt.parse_junit_xml_safe(str(p))
    assert out == {"tests":5,"failures":1,"errors":0}


def test_summarize_test_center_runs_empty():
    # No runs executed yet -> empty list
    out = adm_dt.summarize_test_center_runs(limit=2)
    assert isinstance(out, list)
    assert out == []


def test_artifact_file_readable(tmp_path):
    p = _write(tmp_path, "f.txt", "hello")
    assert adm_dt.artifact_file_readable(str(p)) is True
    assert adm_dt.artifact_file_readable(str(p)+"nope") is False
