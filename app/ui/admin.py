import streamlit as st
from pathlib import Path
from datetime import datetime
from app.core.trade_repo import TradeRepository
from app.analytics.metrics import aggregate_metrics

def load_trades(repo: TradeRepository, path: Path):
    if path.exists():
        repo.import_csv(path)

st.set_page_config(page_title="VekBase Admin", layout="wide")

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

if repo.all():
    metrics = aggregate_metrics(repo.all())
    st.subheader("Key Metrics (Realized)")
    st.json(metrics)
    st.subheader("Positions")
    st.json(repo.positions())

    if st.checkbox("Show Trades Table"):
        rows = [t.to_dict() for t in repo.all()]
        st.dataframe(rows)

st.caption("Personal tool. No enterprise features. ")
