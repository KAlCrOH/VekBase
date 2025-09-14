from app.ui.devtools_output_filter import filter_output_sections


def test_filter_output_sections_basic():
    data = {"stdout": "A", "stderr": "B", "summary": {"passed": 2, "failed": 1}}
    out = filter_output_sections(data, ["stdout", "summary"])
    assert list(out.keys()) == ["stdout", "summary"]
    assert out["stdout"] == "A"
    assert out["summary"]["passed"] == 2
    assert "stderr" not in out


def test_filter_output_sections_unknown_ignored():
    data = {"stdout": "X"}
    out = filter_output_sections(data, ["stdout", "foo", "bar"])  # unknown ignored
    assert list(out.keys()) == ["stdout"]


def test_filter_output_sections_invalid_sections():
    import pytest
    with pytest.raises(ValueError):
        filter_output_sections({"stdout": "x"}, None)  # type: ignore
    with pytest.raises(ValueError):
        filter_output_sections({"stdout": "x"}, 123)  # type: ignore
    with pytest.raises(ValueError):
        filter_output_sections({"stdout": "x"}, [1,2,3])  # type: ignore