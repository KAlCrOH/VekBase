"""
# ============================================================
# Context Banner — console | Category: ui
# Purpose: Zentrale Streamlit Konsole (Trades erfassen, REALIZED Analytics anzeigen, Simulation Runs auslösen, Tests ausführen)

# Contracts
#   Inputs: User Form Eingaben (Trades), Simulation Parameter (steps, seed, momentum window)
#   Outputs: UI Rendering, persistierte Simulationsergebnisse via sim.simple_walk.run_and_persist
#   Side-Effects: File I/O=read/write: data/trades.csv, data/results/*; Network=none
#   Determinism: UI deterministisch außer Zeitstempel für neue Simulationen

# Invariants
#   - Keine Business-Logik (nur Delegation an core/analytics/sim)
#   - Kein Netzwerkzugriff
#   - Persistenzpfade unter ./data/
#   - Zeigt aktuell NUR realized Kennzahlen (unrealized PnL / CAGR / Patterns noch nicht implementiert → siehe Roadmap)

# Dependencies
#   Internal: core.trade_repo, core.trade_model, analytics.metrics, sim.simple_walk
#   External: streamlit, stdlib (pathlib, datetime, subprocess, csv, io)

# Tests
#   Indirekt über Modultests (Analytics, Simulation, Repo). UI selbst nicht unit-getestet.

# Known Gaps
#   - Simulation Erfolgsmeldung erwartet res['folder'], run_and_persist liefert SimResult Objekt (Backlog P0: UI SimResult Rückgabemismatch)

# Do-Not-Change
#   Banner policy-relevant; Änderungen nur via Task „Header aktualisieren“.
# ============================================================
"""
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
import io, csv, subprocess, sys, json, re
from app.core.trade_repo import TradeRepository
from app.core.trade_model import validate_trade_dict, TradeValidationError
from app.analytics.metrics import aggregate_metrics, realized_equity_curve, realized_equity_curve_with_unrealized
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

tabs = st.tabs(["Trades", "Analytics", "Simulation", "DevTools", "Retrieval"])

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
    st.subheader("Analytics (Realized / Unrealized Overlay)")
    if repo.all():
        # Inputs for optional mark prices
        with st.expander("Optional Mark Prices (JSON)", expanded=False):
            mp_text = st.text_area("mark_prices JSON", value="", height=80, help='Format: {"TICKER": price, ...}')
            overlay = st.checkbox("Show Unrealized Overlay", value=False, help="Adds final point including unrealized PnL if open positions.")
        mark_prices = None
        if mp_text.strip():
            try:
                mark_prices = json.loads(mp_text)
                if not isinstance(mark_prices, dict):
                    st.warning("mark_prices must be a JSON object {ticker: price}")
                    mark_prices = None
            except Exception as e:
                st.error(f"JSON parse error: {e}")
        metrics = aggregate_metrics(repo.all(), mark_prices=mark_prices) if mark_prices else aggregate_metrics(repo.all())
        st.json(metrics)
        curve = realized_equity_curve(repo.all())
        import pandas as pd
        if curve:
            df = pd.DataFrame(curve, columns=["ts", "equity_realized"])
            if overlay and mark_prices:
                ext = realized_equity_curve_with_unrealized(repo.all(), mark_prices=mark_prices)
                if len(ext) > len(curve):
                    df2 = pd.DataFrame(ext, columns=["ts", "equity_unrealized_total"])
                    chart_df = df.merge(df2, on="ts", how="outer").set_index("ts").sort_index()
                    st.line_chart(chart_df)
                else:
                    st.line_chart(df.set_index("ts"))
            else:
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
            if res.folder:
                st.success(f"Simulation persisted: {res.folder.name}")
            else:
                st.warning("Simulation run has no folder reference (unexpected)")
            st.json({"meta": res.meta, "final_cash": res.final_cash})
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

# DevTools Tab (extended test runner: discovery + filter + selection)
with tabs[3]:
    st.subheader("DevTools — Test Runner")
    if "test_run_state" not in st.session_state:
        st.session_state.test_run_state = {
            "status": "idle",  # idle|running|passed|failed
            "stdout": "",
            "stderr": "",
            "returncode": None,
            "filter": "",
            "collected": [],  # list of test nodeids
            "selected": set(),  # chosen nodeids
        }
    state = st.session_state.test_run_state
    col_a, col_b, col_c = st.columns([3,1,1])
    with col_a:
        state["filter"] = st.text_input("Pytest -k Filter (expr)", state["filter"], help="Substring expression passed to -k (AND/OR supported)")
    with col_b:
        module_filter = st.text_input("Module (tests/...)", value="", help="Optional path substring e.g. test_metrics")
    with col_c:
        status = state["status"]
        badge_color = {"idle":"grey","running":"orange","passed":"green","failed":"red"}.get(status,"grey")
        st.markdown(f"Status:<br><span style='color:{badge_color};font-weight:bold'>{status}</span>", unsafe_allow_html=True)

    disc_col, run_col, sel_col = st.columns([1,1,2])
    with disc_col:
        if st.button("Discover"):
            # collect tests
            try:
                collect_args = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
                flt = state["filter"].strip()
                if flt:
                    collect_args.extend(["-k", flt])
                if module_filter.strip():
                    collect_args.append(module_filter.strip())
                result = subprocess.run(collect_args, capture_output=True, text=True, timeout=120)
                # Parse nodeids from output lines (pytest -q --collect-only prints them one per line typically)
                lines = [ln.strip() for ln in (result.stdout or "").splitlines() if ln.strip()]
                # Filter out summary lines (which contain 'collected')
                nodeids = [ln for ln in lines if not re.search(r"collected \\d+ items", ln)]
                state["collected"] = nodeids
                # Preserve selection intersection only
                state["selected"] = set([nid for nid in state["selected"] if nid in nodeids])
                state["stdout"] = result.stdout
                state["stderr"] = result.stderr
            except Exception as e:
                state["stderr"] = str(e)
    with run_col:
        run_clicked = st.button("Run All" if not state["selected"] else "Run Selected")
    with sel_col:
        if state["collected"]:
            st.caption(f"Collected: {len(state['collected'])} tests")
            # Multi-select via checkboxes (scrollable expander)
            with st.expander("Select Individual Tests", expanded=False):
                for nid in state["collected"]:
                    checked = nid in state["selected"]
                    new_val = st.checkbox(nid, value=checked, key=f"sel::{nid}")
                    if new_val and not checked:
                        state["selected"].add(nid)
                    elif not new_val and checked:
                        state["selected"].discard(nid)

    if run_clicked and state["status"] != "running":
        state["status"] = "running"
        args = [sys.executable, "-m", "pytest", "-q"]
        # If specific nodeids chosen, append them instead of filter usage
        if state["selected"]:
            args.extend(sorted(state["selected"]))
        flt = state["filter"].strip()
        if flt:
            # Only add -k if no specific selection (selection has precedence)
            if not state["selected"]:
                args.extend(["-k", flt])
        if module_filter.strip() and not state["selected"]:
            args.append(module_filter.strip())
        with st.spinner("Running tests..."):
            try:
                result = subprocess.run(args, capture_output=True, text=True, timeout=120)
                state["stdout"] = result.stdout or ""
                state["stderr"] = result.stderr or ""
                state["returncode"] = result.returncode
                state["status"] = "passed" if result.returncode == 0 else "failed"
            except Exception as e:
                state["stderr"] = str(e)
                state["status"] = "failed"

    # Output panels
    with st.expander("Test Output (stdout)", expanded=True):
        st.code(state["stdout"] or "(empty)")
        # Quick summary: count passes/fails if -q output present
        if state["stdout"]:
            passed = len([ln for ln in state["stdout"].splitlines() if re.search(r"::(PASSED|SKIPPED)", ln, re.IGNORECASE)])
            failed = len([ln for ln in state["stdout"].splitlines() if re.search(r"::(FAILED|ERROR)", ln, re.IGNORECASE)])
            if passed or failed:
                st.markdown(f"**Summary:** ✅ {passed} | ❌ {failed}")
    if state["stderr"]:
        with st.expander("Errors/StdErr"):
            st.code(state["stderr"])
    st.caption("Local only • No network • KISS")

with tabs[4]:
    st.subheader("Retrieval (Context Keyword)")
    st.caption("Lokaler Keyword Retrieval über docs/CONTEXT – keine Embeddings")
    from app.core.retrieval import retrieve as retrieve_ctx
    query = st.text_input("Query", "projekt")
    col_r1, col_r2, col_r3 = st.columns([2,1,1])
    with col_r2:
        ticker_filter = st.text_input("Ticker Filter (optional)", "")
    with col_r3:
        as_of_input = st.text_input("as_of (YYYY-MM-DD optional)", "")
    limit = col_r1.number_input("Limit", min_value=1, max_value=10, value=3, step=1)
    if st.button("Search", key="retrieval_search"):
        as_of_val = as_of_input.strip() or None
        if as_of_val:
            try:
                # simple validation
                datetime.fromisoformat(as_of_val)
            except Exception:
                st.error("Ungültiges as_of Format")
                as_of_val = None
        res = retrieve_ctx(query, limit=limit, ticker=(ticker_filter.strip() or None), as_of=as_of_val)
        if not res:
            st.info("Keine Treffer.")
        else:
            st.dataframe(res)

st.caption("Frontend-first Konsole • Personal Use • KISS")