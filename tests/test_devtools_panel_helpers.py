from app.ui.devtools_panel_helpers import format_queue_rows


def test_format_queue_rows_basic():
    raw = [
        {"run_id": "r1", "status": "passed", "passed": 5, "failed": 0, "duration_s": 1.234},
        {"run_id": "r2", "status": "failed", "passed": 4, "failed": 1},
        {"run_id": "r3", "status": "", "passed": 0},  # missing failed
        {"run_id": "r4"},  # minimal
    ]
    out = format_queue_rows(raw)
    # Ensure length stable
    assert len(out) == 4
    # Check required keys & defaults
    for row in out:
        assert set(["run_id", "status", "passed", "failed"]).issubset(row.keys())
    r3 = next(r for r in out if r["run_id"] == "r3")
    assert r3["status"] == "unknown"  # empty status replaced
    assert r3["failed"] == 0
    r4 = next(r for r in out if r["run_id"] == "r4")
    assert r4["status"] == "unknown" and r4["passed"] == 0 and r4["failed"] == 0


def test_format_queue_rows_invalid():
    import pytest
    with pytest.raises(ValueError):
        format_queue_rows(None)  # type: ignore
    with pytest.raises(ValueError):
        format_queue_rows({})  # type: ignore
    with pytest.raises(ValueError):
        format_queue_rows([1,2,3])  # type: ignore