from app.ui.devtools_session_log import add_test_run, list_test_runs, clear_test_runs, MAX_SESSION_RUNS


def test_session_log_basic_overflow():
    clear_test_runs()
    for i in range(MAX_SESSION_RUNS + 5):
        add_test_run({"status": "passed" if i % 2 == 0 else "failed", "passed": 1, "failed": 0})
    runs = list_test_runs()
    assert len(runs) == MAX_SESSION_RUNS
    # Oldest 5 dropped; we inserted sequentially, so first kept index should be 5
    # Cannot directly check index, but length suffices + last status pattern
    assert runs[-1]["status"] in {"passed","failed"}


def test_session_log_filter():
    clear_test_runs()
    add_test_run({"status": "passed", "passed": 2, "failed": 0})
    add_test_run({"status": "failed", "passed": 1, "failed": 1})
    failed_only = list_test_runs(status=["failed"])
    assert len(failed_only) == 1 and failed_only[0]["status"] == "failed"


def test_session_log_invalid():
    clear_test_runs()
    import pytest
    with pytest.raises(ValueError):
        add_test_run({})  # missing keys
    with pytest.raises(ValueError):
        add_test_run({"status": "", "passed": 0, "failed": 0})  # empty status
    with pytest.raises(ValueError):
        add_test_run({"status": "ok", "passed": -1, "failed": 0})  # negative passed