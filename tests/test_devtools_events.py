import os
from app.ui.devtools_events import emit, get_events, clear_events


def test_events_flag_off(monkeypatch):
    monkeypatch.setenv("VEK_DEVTOOLS_VERBOSE", "0")
    clear_events()
    stored = emit("test_run", {"passed": 1})
    assert stored is False
    assert get_events() == []


def test_events_flag_on(monkeypatch):
    monkeypatch.setenv("VEK_DEVTOOLS_VERBOSE", "1")
    clear_events()
    for i in range(105):  # exceed ring size
        emit("run", {"i": i})
    ev = get_events()
    assert len(ev) == 100  # ring buffer size
    # Ensure oldest events dropped (i starts at 0; earliest kept should be 5)
    earliest = min(e["payload"]["i"] for e in ev)
    assert earliest >= 5
    latest = max(e["payload"]["i"] for e in ev)
    assert latest == 104


def test_events_invalid_payload(monkeypatch):
    monkeypatch.setenv("VEK_DEVTOOLS_VERBOSE", "1")
    clear_events()
    import pytest
    with pytest.raises(ValueError):
        emit("", {})  # empty event
    with pytest.raises(ValueError):
        emit("x", 123)  # type: ignore
