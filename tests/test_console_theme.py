"""
# ============================================================
# Context Banner — test_console_theme | Category: test
# Purpose: Validate dark mode Altair theme helper for console charts.
# ============================================================
"""
import os
import altair as alt
from app.ui.console_theme import apply_console_theme


def _simple_chart():
    import pandas as pd
    df = pd.DataFrame({"ts": ["2024-01-01", "2024-01-02"], "val": [1,2]})
    return alt.Chart(df).mark_line().encode(x="ts:T", y="val:Q")


def test_console_theme_light(monkeypatch):
    monkeypatch.delenv("VEK_CONSOLE_DARK", raising=False)
    ch = apply_console_theme(_simple_chart())
    spec = ch.to_dict()
    # Light mode should not set custom dark background
    bg = spec.get("config", {}).get("background")
    assert bg is None or bg not in ("#081018", "#080910")


def test_console_theme_dark(monkeypatch):
    monkeypatch.setenv("VEK_CONSOLE_DARK", "1")
    ch = apply_console_theme(_simple_chart())
    spec = ch.to_dict()
    assert spec.get("config", {}).get("background") == "#081018"