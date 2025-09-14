from app.ui.devtools_audit_export import build_last_run_payload, export_json, export_csv


def test_audit_export_full():
    state = {
        "status": "passed",
        "summary": {"passed": 3, "failed": 0},
        "stdout": "test_a::PASSED\n",
        "stderr": "",
    }
    payload = build_last_run_payload(state)
    assert payload and payload["passed"] == 3
    js = export_json(state)
    assert js and '"passed": 3' in js
    csv_txt = export_csv(state)
    assert csv_txt and 'passed,failed,stdout_lines,stderr_lines' in csv_txt.splitlines()[0]


def test_audit_export_missing():
    state = {"status": "idle", "summary": {}}  # incomplete
    assert build_last_run_payload(state) is None
    assert export_json(state) is None
    assert export_csv(state) is None


def test_audit_export_invalid_state():
    import pytest
    with pytest.raises(ValueError):
        build_last_run_payload(None)  # type: ignore