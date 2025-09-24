"""
# ============================================================
# Context Banner — admin | Category: cli
# Purpose: Frühere einfache Admin-Ansicht (legacy) für Metrics/Trades vor Einführung der Konsole

# Contracts
#   Inputs: trades.csv falls vorhanden
#   Outputs: Streamlit Darstellung (Metrics, Positions, optional Tabelle)
#   Side-Effects: File I/O read: data/trades.csv; DevTools writes: data/devtools/* (bench baselines, snapshots, testqueue persistence); Network=none
#   Determinism: deterministic (abhängig von Dateiinhalt)

# Invariants
#   - Keine Schreiboperationen (read-only display)
#   - Business-Logik delegiert an core/analytics

# Dependencies
#   Internal: core.trade_repo, analytics.metrics
#   External: streamlit

# Tests
#   Keiner direkt; abgelöst durch console.py (Konsole übernimmt Funktionalität)

# Do-Not-Change
#   Banner policy-relevant; Änderungen nur via Task „Header aktualisieren“.
# ============================================================
"""
import streamlit as st
from pathlib import Path
from datetime import datetime

# Direct imports (Bootstrap removed after packaging migration)
from app.core.trade_repo import TradeRepository  # type: ignore
from app.analytics.metrics import aggregate_metrics  # type: ignore
from app.core.default_data import load_default_trades  # type: ignore

def load_trades(repo: TradeRepository, path: Path):
    if path.exists():
        repo.import_csv(path)

st.set_page_config(page_title="VekBase Admin", layout="wide")

import os

st.title("VekBase Admin")

data_dir = Path("data")
trades_path = data_dir / "trades.csv"

repo = TradeRepository()
if trades_path.exists():
    try:
        repo.import_csv(trades_path)
        st.success(f"Loaded {len(repo.all())} trades from trades.csv")
    except Exception as e:
        st.error(f"Error loading trades: {e}")
else:
    st.warning("No data/trades.csv found. Please add your trade file.")

# Default dataset auto-load (VEK_DEFAULT_DATA=1)
if not repo.all() and bool(int(os.environ.get("VEK_DEFAULT_DATA", "1"))):
    added = load_default_trades(repo)
    if added:
        st.caption(f"Default demo dataset loaded ({added} trades) — disable via VEK_DEFAULT_DATA=0")

if repo.all():
    metrics = aggregate_metrics(repo.all())
    st.subheader("Key Metrics (Realized)")
    st.json(metrics)
    st.subheader("Positions")
    st.json(repo.positions())

    if st.checkbox("Show Trades Table"):
        rows = [t.to_dict() for t in repo.all()]
        st.dataframe(rows)

st.markdown("---")
st.caption("(Legacy admin view trimmed. DevTools, Retrieval, DecisionCards panels removed in investor-focused redesign.)")
st.caption("Personal tool. No enterprise features.")
