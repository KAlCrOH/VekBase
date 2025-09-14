"""
# ============================================================
# Context Banner — console_theme | Category: ui
# Purpose: Theme helper for console Altair charts (light/dark) decoupled from Streamlit for unit testing.
#
# Contracts
#   apply_console_theme(chart, dark:bool|None=None) -> alt.Chart (possibly themed)
#     - dark None => reads env VEK_CONSOLE_DARK == '1'
#
# Invariants
#   - Pure (no mutation of incoming chart; returns configured chart)
#   - No Streamlit dependency
#
# Tests
#   tests/test_console_theme.py
# ============================================================
"""
from __future__ import annotations
import os
from typing import Optional

def apply_console_theme(chart, dark: Optional[bool] = None):  # alt.Chart duck-typed
    if dark is None:
        dark = os.getenv("VEK_CONSOLE_DARK") == "1"
    if not dark:
        return chart
    # Apply simple dark theme adjustments
    themed = (
        chart.configure(
            background="#081018",
        )
        .configure_axis(labelColor="#e0e0e0", titleColor="#e0e0e0")
        .configure_legend(labelColor="#e0e0e0", titleColor="#e0e0e0")
        .configure_view(stroke="#283040")
    )
    return themed

__all__ = ["apply_console_theme"]
