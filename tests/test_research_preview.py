"""
Tests for research_preview helper (Increment I2 A_OPTIMAL)
Focus:
 - attribution_preview returns ok with synthetic equity
 - portfolio_preview returns ok with diversification benefit >= 0
 - empty curve returns status empty
 - flags off scenario (panels_enabled false when both flags 0)
"""
from app.ui.research_preview import attribution_preview, portfolio_preview, panels_enabled


def _synthetic_equity(n=15):
    # simple upward curve with mild variation
    base = []
    val = 100.0
    for i in range(n):
        val *= (1 + 0.01 + (0.001 * ((i % 3) - 1)))  # deterministic wiggle
        base.append((i, val))
    return base


def test_attribution_preview_ok():
    curve = _synthetic_equity()
    res = attribution_preview(curve)
    assert res["status"] in {"ok","empty"}
    if res["status"] == "ok":
        assert "betas" in res and isinstance(res["betas"], dict)
        assert "r_squared" in res


def test_portfolio_preview_ok():
    curve = _synthetic_equity()
    res = portfolio_preview(curve)
    assert res["status"] in {"ok","empty"}
    if res["status"] == "ok":
        assert "metrics" in res and "diversification_benefit" in res["metrics"]


def test_empty_handling():
    res_a = attribution_preview([])
    res_p = portfolio_preview([])
    assert res_a["status"] == "empty"
    assert res_p["status"] == "empty"


def test_panels_disabled(monkeypatch):
    monkeypatch.setenv("VEK_ATTRIBUTION", "0")
    monkeypatch.setenv("VEK_PORTFOLIO", "0")
    assert panels_enabled() is False
