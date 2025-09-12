"""
# ============================================================
# Context Banner — console | Category: cli
# Purpose: Zentrale Streamlit Konsole (Trades erfassen, Analytics anzeigen, Simulation Runs auslösen, Tests ausführen)

# Contracts
#   Inputs: User Form Eingaben (Trades), Simulation Parameter (steps, seed, momentum window)
#   Outputs: UI Rendering, persistierte Simulationsergebnisse via sim.simple_walk.run_and_persist
#   Side-Effects: File I/O=read/write: data/trades.csv, data/results/*; Network=none
#   Determinism: UI deterministisch außer Zeitstempel für neue Simulationen

# Invariants
#   - Keine Business-Logik (nur Delegation an core/analytics/sim)
#   - Kein Netzwerkzugriff
#   - Persistenzpfade unter ./data/

# Dependencies
#   Internal: core.trade_repo, core.trade_model, analytics.metrics, sim.simple_walk
#   External: streamlit, stdlib (pathlib, datetime, subprocess, csv, io)

# Tests
#   Indirekt über Modultests (Analytics, Simulation, Repo). UI selbst nicht unit-getestet.

# Do-Not-Change
#   Banner policy-relevant; Änderungen nur via Task „Header aktualisieren“.
# ============================================================
"""
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
import io, csv, subprocess, sys
from app.core.trade_repo import TradeRepository
from app.core.trade_model import validate_trade_dict, TradeValidationError
from app.analytics.metrics import aggregate_metrics, realized_equity_curve
from app.sim.simple_walk import run_and_persist, momentum_rule

st.set_page_config(page_title="VekBase Console", layout="wide")

st.title("VekBase Frontend Zentrale (MVP)")

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
trades_path = data_dir / "trades.csv"
results_dir = data_dir / "results"
results_dir.mkdir(exist_ok=True)

repo = TradeRepository()
if trades_path.exists():
    try:
        repo.import_csv(trades_path)
        st.success(f"Loaded {len(repo.all())} trades")
    except Exception as e:
        st.error(f"Import error: {e}")
else:
    st.info("No trades.csv yet. Add trades via the form below and click Save.")

tabs = st.tabs(["Trades", "Analytics", "Simulation", "DevTools"])

# Trades Tab
with tabs[0]:
    st.subheader("Trade Erfassung")
    with st.form("trade_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        trade_id = c1.text_input("trade_id", value=f"t{len(repo.all())+1}")
        ts = c2.text_input("ts (ISO)", value=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        ticker = c3.text_input("ticker").upper()
        action = c4.selectbox("action", ["BUY", "SELL"], index=0)
        c5, c6, c7, c8 = st.columns(4)
        shares = c5.number_input("shares", min_value=0.0001, value=1.0, format="%f")
        price = c6.number_input("price", min_value=0.0, value=0.0, format="%f")
        fees = c7.number_input("fees", min_value=0.0, value=0.0, format="%f")
        tag = c8.text_input("tag", value="")
        submitted = st.form_submit_button("Add Trade")
        if submitted:
            raw = {
                "trade_id": trade_id,
                "ts": ts,
                "ticker": ticker,
                "action": action,
                "shares": shares,
                "price": price,
                "fees": fees,
                "tag": tag or None,
            }
            try:
                trade = validate_trade_dict(raw)
                repo.add_trade(trade)
                st.success(f"Added trade {trade.trade_id}")
            except TradeValidationError as e:
                st.error(f"Validation failed: {e}")
    st.markdown("### Aktuelle Trades")
    if repo.all():
        st.dataframe([t.to_dict() for t in repo.all()])
        if st.button("Speichern (CSV)"):
            try:
                repo.export_csv(trades_path)
                st.success("CSV gespeichert")
            except Exception as e:
                st.error(f"Export Fehler: {e}")

# Analytics Tab
with tabs[1]:
    st.subheader("Analytics (Realized)")
    if repo.all():
        metrics = aggregate_metrics(repo.all())
        st.json(metrics)
        curve = realized_equity_curve(repo.all())
        if curve:
            import pandas as pd
            df = pd.DataFrame(curve, columns=["ts", "equity"])
            st.line_chart(df.set_index("ts"))
    else:
        st.info("Keine Trades geladen.")

# Simulation Tab + persistence
with tabs[2]:
    st.subheader("Simulation Runs")
    st.caption("Deterministische Walk-Forward Dummy Strategie mit Persistenz")
    with st.form("sim_form"):
        steps = st.number_input("Steps", min_value=5, max_value=1000, value=50, step=5)
        seed = st.number_input("Seed", min_value=0, max_value=999999, value=42, step=1)
        rule_window = st.number_input("Momentum Window", min_value=2, max_value=50, value=5, step=1)
        submitted_sim = st.form_submit_button("Run Simulation & Persist")
    if submitted_sim:
        # construct synthetic price series
        base = 100.0
        prices = []
        for i in range(steps):
            ts_i = datetime(2024,1,1) + timedelta(minutes=i)
            price = base + i * 0.1  # simple upward drift
            prices.append((ts_i, price))
        try:
            res = run_and_persist(prices, momentum_rule(rule_window), seed=seed, results_dir=results_dir)
            st.success(f"Simulation persisted: {res['folder']}")
            st.json({k: v for k, v in res.items() if k != 'folder'})
        except Exception as e:
            st.error(f"Simulation error: {e}")
    # list last few runs
    if results_dir.exists():
        runs = sorted([p for p in results_dir.iterdir() if p.is_dir()], reverse=True)[:5]
        if runs:
            st.markdown("#### Letzte Runs")
            for r in runs:
                meta_file = r / 'meta.json'
                equity_file = r / 'equity.csv'
                if meta_file.exists():
                    st.write(r.name)
                    with meta_file.open('r', encoding='utf-8') as f:
                        st.code(f.read(), language='json')
                if equity_file.exists() and st.checkbox(f"Equity anzeigen: {r.name}", key=r.name):
                    import pandas as pd
                    df = pd.read_csv(equity_file)
                    st.line_chart(df.set_index('ts'))

# DevTools Tab
with tabs[3]:
    st.subheader("DevTools — Test Runner")
    if st.button("Run Pytests"):
        with st.spinner("Running tests..."):
            try:
                result = subprocess.run([sys.executable, "-m", "pytest", "-q"], capture_output=True, text=True, timeout=60)
                st.code(result.stdout or "(no stdout)")
                if result.stderr:
                    st.error(result.stderr)
                if result.returncode == 0:
                    st.success("Tests passed")
                else:
                    st.error(f"Tests failed (exit {result.returncode})")
            except Exception as e:
                st.error(f"Error running tests: {e}")
    st.caption("Local only • No network • KISS")

st.caption("Frontend-first Konsole • Personal Use • KISS")