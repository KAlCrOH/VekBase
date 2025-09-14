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
#   - Unrealized Equity Curve Erweiterung (vollständige Integration) (Backlog #7)
#   - Erweiterte Simulation Parameter (TP/SL/Kosten) (Backlog #5)
#   - Erweiterte Pattern Analytics (beyond basic histogram/scatter) (Backlog #8 PARTIAL)
#   - Snapshot Regression Test Coverage Ausbau (Backlog #9 PARTIAL)
#   - Aggregierte Queue Metriken & Retention Policy (Neue Backlog Items)

# Do-Not-Change
#   Banner policy-relevant; Änderungen nur via Task „Header aktualisieren“.
# ============================================================
"""
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
import io, csv, subprocess, sys, json, re, os

# Direct imports (Bootstrap removed after packaging migration)
from app.core.trade_repo import TradeRepository  # type: ignore
from app.core.trade_model import validate_trade_dict, TradeValidationError  # type: ignore
from app.analytics.metrics import aggregate_metrics, realized_equity_curve, realized_equity_curve_with_unrealized, unrealized_equity_timeline  # type: ignore
from app.core.default_data import load_default_trades  # type: ignore
from app.sim.simple_walk import run_and_persist, momentum_rule  # type: ignore

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

# Default dataset auto-load (feature flag VEK_DEFAULT_DATA=1)
if not repo.all() and bool(int(os.environ.get("VEK_DEFAULT_DATA", "1"))):
    added = load_default_trades(repo)
    if added:
        st.caption(f"Default demo dataset loaded ({added} trades) — disable via VEK_DEFAULT_DATA=0")

devtools_enabled = bool(int(os.environ.get("VEK_DEVTOOLS", "1")))
decision_cards_enabled = bool(int(os.environ.get("VEK_DECISIONCARDS", "1")))
patterns_enabled = bool(int(os.environ.get("VEK_PATTERNS", "1")))
analytics_ext_enabled = bool(int(os.environ.get("VEK_ANALYTICS_EXT", "0")))
workbench_enabled = True  # always enable for roadmap visualization
tabs = st.tabs([
    "Trades",
    "Analytics",
    "Simulation",
    "DevTools" if devtools_enabled else "DevTools (disabled)",
    "Retrieval",
    "DecisionCards" if decision_cards_enabled else "DecisionCards (disabled)",
    "Workbench"
])

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
    st.subheader("Analytics (Equity / Unrealized / Benchmark)")
    if repo.all():
        # Unified overlay inputs
        with st.expander("Overlay Inputs (Marks & Benchmark)", expanded=False):
            mp_text = st.text_area(
                "mark_prices JSON",
                value="",
                height=80,
                help='Format: {"TICKER": price, ...} — used to compute unrealized and total equity.'
            )
            bm_text = st.text_area(
                "benchmark JSON",
                value="",
                height=80,
                help=(
                    "Accepted formats: {\"ISO_TS\": value, ...} OR [[\"ISO_TS\", value], ...] OR simple list of values (aligned to realized equity timestamps)."
                )
            )
            c_ov1, c_ov2, c_ov3 = st.columns(3)
            overlay = c_ov1.checkbox(
                "Include Unrealized / Total",
                value=False,
                help="Adds unrealized equity (open positions) and combined total (realized+unrealized)."
            )
            show_benchmark = c_ov2.checkbox(
                "Show Benchmark",
                value=bool(bm_text.strip()),
                help="Overlay benchmark series if provided."
            )
            show_vol = c_ov3.checkbox(
                "Rolling Volatility",
                value=False,
                help="Plot rolling volatility of realized equity (window=5 points)."
            )
        # Parse mark prices
        mark_prices = None
        if mp_text.strip():
            try:
                mark_prices = json.loads(mp_text)
                if not isinstance(mark_prices, dict):
                    st.warning("mark_prices must be a JSON object {ticker: price}")
                    mark_prices = None
            except Exception as e:
                st.error(f"mark_prices JSON parse error: {e}")
        # Parse benchmark
        benchmark_series = None  # list of (ts,value)
        if bm_text.strip():
            try:
                raw_bm = json.loads(bm_text)
                import pandas as _pd  # local alias
                if isinstance(raw_bm, dict):
                    # keys are timestamps
                    benchmark_series = sorted([(k, raw_bm[k]) for k in raw_bm.keys()])
                elif isinstance(raw_bm, list):
                    if raw_bm and all(isinstance(x, list) and len(x) == 2 for x in raw_bm):
                        benchmark_series = [(x[0], x[1]) for x in raw_bm]
                    elif raw_bm and all(isinstance(x, (int, float)) for x in raw_bm):
                        # align to realized equity timestamps later
                        benchmark_series = [(None, v) for v in raw_bm]
                else:
                    st.warning("Unsupported benchmark JSON format")
            except Exception as e:
                st.error(f"benchmark JSON parse error: {e}")
        # Metrics summary
        metrics = aggregate_metrics(repo.all(), mark_prices=mark_prices) if mark_prices else aggregate_metrics(repo.all())
        st.json(metrics)
        curve = realized_equity_curve(repo.all())
        import pandas as pd
        if curve:
            base_df = pd.DataFrame(curve, columns=["ts", "equity_realized"]).sort_values("ts")
            # Build unrealized + total if requested
            if overlay and mark_prices:
                unreal_tl = unrealized_equity_timeline(repo.all(), mark_prices=mark_prices) or []
                if unreal_tl:
                    df_unr = pd.DataFrame(unreal_tl, columns=["ts", "equity_unrealized"])  # unrealized open positions value
                    ext = realized_equity_curve_with_unrealized(repo.all(), mark_prices=mark_prices)
                    if len(ext) >= len(curve):
                        df_total = pd.DataFrame(ext, columns=["ts", "equity_total"]).sort_values("ts")
                    else:
                        df_total = None
                else:
                    df_unr = None
                    df_total = None
            else:
                df_unr = None
                df_total = None
            # Benchmark DataFrame
            df_bm = None
            if show_benchmark and benchmark_series:
                # If timestamps missing (aligned list), map onto realized curve timestamps
                if benchmark_series and benchmark_series[0][0] is None:
                    ts_list = list(base_df["ts"].values)
                    vals = [v for (_, v) in benchmark_series]
                    if len(vals) != len(ts_list):
                        st.warning("Benchmark value count does not match realized equity points; truncating to shortest length.")
                    n = min(len(vals), len(ts_list))
                    df_bm = pd.DataFrame({"ts": ts_list[:n], "benchmark": vals[:n]})
                else:
                    df_bm = pd.DataFrame(benchmark_series, columns=["ts", "benchmark"]).sort_values("ts")
            # Merge all
            frames = [base_df]
            if df_unr is not None:
                frames.append(df_unr)
            if df_total is not None:
                frames.append(df_total)
            if df_bm is not None:
                frames.append(df_bm)
            full = None
            for f in frames:
                if full is None:
                    full = f
                else:
                    full = full.merge(f, on="ts", how="outer")
            if full is not None:
                full = full.sort_values("ts")
                # Rolling volatility (window=5) if requested
                if show_vol:
                    try:
                        from app.analytics.metrics import rolling_volatility as _roll_vol
                        rv = _roll_vol([(row.ts, row.equity_realized) for row in full.itertuples() if not pd.isna(row.equity_realized)], window=5)
                        if rv:
                            df_rv = pd.DataFrame(rv, columns=["ts","rolling_volatility"]).sort_values("ts")
                            full = full.merge(df_rv, on="ts", how="left")
                    except Exception as e:
                        st.warning(f"Rolling volatility error: {e}")
                # Altair multi-series chart
                try:
                    import altair as alt
                    melt_cols = [c for c in [
                        "equity_realized",
                        "equity_unrealized" if df_unr is not None else None,
                        "equity_total" if df_total is not None else None,
                        "benchmark" if df_bm is not None else None,
                        "rolling_volatility" if show_vol else None,
                    ] if c]
                    plot_df = full.melt(id_vars="ts", value_vars=melt_cols, var_name="series", value_name="value")
                    # Drop NaNs
                    plot_df = plot_df.dropna(subset=["value"])  # type: ignore
                    from .console_theme import apply_console_theme
                    base_chart = alt.Chart(plot_df).mark_line(point=False).encode(
                        x=alt.X("ts:T", title="Timestamp"),
                        y=alt.Y("value:Q", title="Value"),
                        color=alt.Color("series:N", legend=alt.Legend(title="Series")),
                        tooltip=["ts:T","series:N","value:Q"],
                    ).properties(height=400)
                    base_chart = apply_console_theme(base_chart)
                    st.altair_chart(base_chart, use_container_width=True)
                except Exception as e:
                    st.warning(f"Altair chart fallback (reason: {e})")
                    st.line_chart(full.set_index("ts"))
            else:
                st.info("No equity data to plot.")
        # Pattern Analytics (Histogram + Scatter) behind feature flag
        st.markdown("---")
        st.subheader("Pattern Analytics (Holding Duration & Entry→Return)")
        if not patterns_enabled:
            st.info("Patterns disabled (VEK_PATTERNS=0)")
        else:
            from app.analytics.patterns import holding_duration_histogram, entry_return_scatter
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                bucket_minutes = st.number_input("Bucket Minutes", min_value=1, max_value=240, value=60, step=5, key="pat_bucket")
                max_buckets = st.number_input("Max Buckets", min_value=1, max_value=20, value=10, step=1, key="pat_buckets")
                _hist_res = holding_duration_histogram(repo.all(), bucket_minutes=int(bucket_minutes), max_buckets=int(max_buckets))
                # backward compatibility: accept list or dict
                if isinstance(_hist_res, dict):
                    counts = _hist_res.get('buckets', [])
                    p50 = _hist_res.get('p50')
                    p90 = _hist_res.get('p90')
                else:  # legacy list
                    counts = _hist_res
                    p50 = p90 = None
                st.caption("Holding Duration Histogram (bucket counts)")
                import pandas as pd
                dfh = pd.DataFrame({"bucket": list(range(len(counts))), "count": counts}).set_index("bucket")
                st.bar_chart(dfh)
                if p50 is not None:
                    st.caption(f"Durations p50={p50:.1f}m p90={p90:.1f}m (bucket={int(bucket_minutes)}m)")
            with col_p2:
                pts = entry_return_scatter(repo.all())
                if pts:
                    import pandas as pd
                    dfp = pd.DataFrame(pts, columns=["entry_price","return_pct"])
                    st.scatter_chart(dfp, x="entry_price", y="return_pct")
                else:
                    st.info("No closed positions to plot.")
        # Extended analytics (optional)
        if analytics_ext_enabled:
            st.markdown("---")
            st.subheader("Extended Analytics (Flag VEK_ANALYTICS_EXT=1)")
            from app.analytics.patterns import return_distribution as _ret_dist
            from app.analytics.metrics import drawdown_curve as _dd_curve, position_size_series as _pos_series
            ec1, ec2 = st.columns(2)
            with ec1:
                # Drawdown chart
                eq_curve = realized_equity_curve(repo.all())
                if eq_curve:
                    dd = _dd_curve(eq_curve)
                    if dd:
                        import pandas as pd
                        dfdd = pd.DataFrame(dd, columns=["ts","drawdown"]).set_index("ts")
                        st.caption("Realized Drawdown Curve")
                        st.line_chart(dfdd)
                # Position size series
                pos_series = _pos_series(repo.all())
                if pos_series:
                    import pandas as pd
                    dfpos = pd.DataFrame(pos_series)
                    dfpos = dfpos.set_index("ts")
                    st.caption("Gross Exposure Over Time (Shares * Price)")
                    st.area_chart(dfpos["gross_exposure"])
            with ec2:
                # Return distribution
                bucket_size = st.number_input("Return Bucket Size", min_value=0.001, max_value=0.2, value=0.01, step=0.001, format="%.3f", key="ret_bucket")
                dist = _ret_dist(repo.all(), bucket_size=float(bucket_size))
                if dist.get('buckets'):
                    import pandas as pd
                    dfb = pd.DataFrame([
                        {"mid": (b['start']+b['end'])/2.0, "count": b['count']} for b in dist['buckets'] if b['count'] > 0
                    ])
                    if not dfb.empty:
                        dfb = dfb.set_index("mid")
                        st.caption("Realized Return Distribution (portion-wise)")
                        st.bar_chart(dfb)
                else:
                    st.info("No realized returns yet for distribution.")
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

from app.ui import devtools_shared as _dshared  # unified wrappers

# DevTools Tab (refactored to use app.core.devtools)
with tabs[3]:
    st.subheader("DevTools — Test Runner")
    if not devtools_enabled:
        st.info("DevTools deaktiviert (VEK_DEVTOOLS=0). Setze Env Var um zu aktivieren.")
    else:
        if "dt_state" not in st.session_state:
            st.session_state.dt_state = {
                "status": "idle",  # idle|running|passed|failed|error
                "stdout": "",
                "stderr": "",
                "filter": "",
                "module": "",
                "collected": [],
                "selected": set(),
            }
        s = st.session_state.dt_state
        c1, c2, c3 = st.columns([3,1,1])
        with c1:
            s["filter"] = st.text_input("Pytest -k Filter", s["filter"], help="Expression for -k (optional)")
        with c2:
            s["module"] = st.text_input("Module Substr", s["module"], help="e.g. test_metrics")
        with c3:
            badge_color = {"idle":"grey","running":"orange","passed":"green","failed":"red","error":"red"}.get(s["status"],"grey")
            st.markdown(f"Status:<br><span style='color:{badge_color};font-weight:bold'>{s['status']}</span>", unsafe_allow_html=True)

        col_d, col_r, col_sel = st.columns([1,1,2])
        with col_d:
            if st.button("Discover"):
                try:
                    nodeids = _dshared.discover_tests(k_expr=s["filter"].strip() or None, module_substr=s["module"].strip() or None)
                    s["collected"] = nodeids
                    # keep only still valid selections
                    s["selected"] = set([nid for nid in s["selected"] if nid in nodeids])
                except Exception as e:
                    s["stderr"] = str(e)
                    s["collected"] = []
        with col_r:
            run_clicked = st.button("Run Selected" if s["selected"] else "Run (Filter)")
        with col_sel:
            if s["collected"]:
                st.caption(f"Collected: {len(s['collected'])}")
                with st.expander("Select Tests", expanded=False):
                    for nid in s["collected"]:
                        chk = st.checkbox(nid, value=(nid in s["selected"]), key=f"dt::{nid}")
                        if chk:
                            s["selected"].add(nid)
                        else:
                            s["selected"].discard(nid)

        if run_clicked and s["status"] != "running":
            s["status"] = "running"
            with st.spinner("Running tests..."):
                res = _dshared.run_tests(nodeids=sorted(s["selected"]) if s["selected"] else None,
                                          k_expr=s["filter"].strip() or None,
                                          module_substr=s["module"].strip() or None)
            s["stdout"], s["stderr"], s["status"] = res["stdout"], res["stderr"], res["status"]

        with st.expander("Test Output", expanded=True):
            st.code(s["stdout"] or "(empty)")
            if s["stdout"]:
                if res["passed"] or res["failed"]:
                    st.markdown(f"**Summary:** ✅ {res['passed']} | ❌ {res['failed']}")
        if s["stderr"]:
            with st.expander("Errors/StdErr"):
                st.code(s["stderr"])
        # Lint Panel
        st.markdown("---")
        st.subheader("Lint Checks (Lightweight)")
        if "lint_state" not in st.session_state:
            st.session_state.lint_state = {"running": False, "report": None}
        ls = st.session_state.lint_state
        col_l1, col_l2 = st.columns([1,3])
        with col_l1:
            lint_clicked = st.button("Run Lint", disabled=ls["running"], key="lint_run")
        with col_l2:
            st.caption("Prüft Syntax, trailing whitespace, mixed indentation (lokal)")
        if lint_clicked:
            ls["running"] = True
            with st.spinner("Linting..."):
                report = _dshared.run_lint()
            ls["report"] = report
            ls["running"] = False
        if ls.get("report"):
            rep = ls["report"]
            st.markdown(f"**Issues:** {rep['total']} (Errors: {rep['errors']} / Warnings: {rep['warnings']})")
            if rep['issues']:
                import pandas as pd
                st.dataframe(pd.DataFrame(rep['issues']))
        st.caption("Local only • No network • KISS")
        # Benchmark Panel
        st.markdown("---")
        st.subheader("Benchmarks (Median ms)")
        if "bench_state" not in st.session_state:
            st.session_state.bench_state = {"report": None, "target": "aggregate_metrics", "repeat": 3}
        bs = st.session_state.bench_state
        reg = _dshared.list_benchmarks()
        if reg:
            bs["target"] = st.selectbox(
                "Target",
                list(reg.keys()),
                index=list(reg.keys()).index(bs["target"]) if bs["target"] in reg else 0,
                help="Registered benchmark target",
            )
            bs["repeat"] = st.number_input("Repeat", min_value=1, max_value=20, value=bs["repeat"], step=1)
            if st.button("Run Benchmark"):
                res = _dshared.run_benchmark(bs["target"], repeat=int(bs["repeat"]))
                bs["report"] = res
            if bs.get("report"):
                r = bs["report"]
                st.json(r)
                if r.get("delta_pct") is not None:
                    delta = r["delta_pct"]
                    st.markdown(
                        f"Delta vs baseline: {delta:+.2f}% {'(faster)' if r.get('faster') else '(slower)' if delta else ''}"
                    )
        else:
            st.info("No benchmark targets registered")
        st.caption("Benchmarks lokal & deterministisch (sample trades)")
        # Snapshot Regression Panel
        st.markdown("---")
        st.subheader("Snapshots (Regression)")
        if "snapshot_state" not in st.session_state:
            st.session_state.snapshot_state = {"target": "metrics", "result": None, "update": False}
        ss = st.session_state.snapshot_state
        snapshot_targets = ["metrics","equity_curve","equity_curve_unrealized","equity_curve_per_ticker"]
        # default fallback if previous selection not in new list
        if ss["target"] not in snapshot_targets:
            ss["target"] = "metrics"
        ss["target"] = st.selectbox("Snapshot Target", snapshot_targets, index=snapshot_targets.index(ss["target"]))
        ss["update"] = st.checkbox("Update Baseline if Diff", value=ss.get("update", False))
        if st.button("Run Snapshot"):
            res = _dshared.snapshot(ss["target"], update=ss["update"])
            ss["result"] = res
        if ss.get("result"):
            res = ss["result"]
            summary = res.get("summary") if isinstance(res, dict) else None
            if summary:
                st.markdown(
                    f"Status: **{summary['status']}** | Diff Count: {summary['diff_count']} | Updated: {summary['updated']}"
                )
            st.json(res)
            if res.get("status") == "diff":
                st.warning("Differences detected — review before updating baseline.")
            nd = res.get("numeric_deltas") if isinstance(res, dict) else None
            if nd:
                try:
                    import pandas as pd
                    st.markdown("**Numeric Deltas**")
                    st.dataframe(pd.DataFrame(nd))
                except Exception:
                    st.caption("(numeric deltas table unavailable)")
        st.caption("Snapshots verwenden deterministische Sample Trades; Baselines unter data/devtools/snapshots/")
        # Queued Test Runner Panel (Portierung aus Admin, Auto-Refresh)
        st.markdown("---")
        st.subheader("Queued Test Runner")
        from app.ui import admin_devtools as _adm_dt
        if "queue_state" not in st.session_state:
            st.session_state.queue_state = {"filter": "metrics", "runs": [], "last_id": None, "auto": True, "interval": 5, "last_poll": 0.0}
        qs = st.session_state.queue_state
        qc1, qc2, qc3, qc4, qc5 = st.columns([3,1,1,1,1])
        with qc1:
            qs["filter"] = st.text_input("Queue -k Filter", qs["filter"], key="cons_q_filter")
        with qc2:
            if st.button("Queue Run", key="cons_q_submit"):
                qs["last_id"] = _adm_dt.submit_test_run(k_expr=qs["filter"].strip() or None)
        with qc3:
            qs["auto"] = st.checkbox("Auto", value=qs.get("auto", True), key="cons_q_auto")
        with qc4:
            qs["interval"] = st.number_input("Interval s", min_value=2, max_value=60, value=int(qs.get("interval",5)), step=1, key="cons_q_int")
        with qc5:
            qs["status_filter"] = st.multiselect("Status", ["queued","running","passed","failed","error"], default=qs.get("status_filter",[]), key="cons_q_status")
        qs["show_persisted"] = st.checkbox("Persisted", value=qs.get("show_persisted", True), key="cons_q_persisted")
        if st.button("Refresh Now", key="cons_q_refresh"):
            qs["runs"] = _adm_dt.list_test_runs(limit=25, status=qs.get("status_filter") or None, include_persisted=qs.get("show_persisted", True))
            import time as _time
            qs["last_poll"] = _time.time()
        import time as _time
        now_q = _time.time()
        if qs.get("auto") and (now_q - qs.get("last_poll",0) >= qs.get("interval",5)):
            qs["runs"] = _adm_dt.list_test_runs(limit=25, status=qs.get("status_filter") or None, include_persisted=qs.get("show_persisted", True))
            qs["last_poll"] = now_q
        if qs.get("runs"):
            rows = qs["runs"]
            try:
                import pandas as pd
                df = pd.DataFrame(rows)
                cols = [c for c in ["run_id","status","passed","failed","duration_s","queued_at","started_at","finished_at","stdout_truncated","stderr_truncated"] if c in df.columns]
                st.dataframe(df[cols])
            except Exception:
                st.json(rows)
            ec1, ec2, ec3 = st.columns([1,1,1])
            with ec1:
                if st.button("Export JSON", key="cons_q_export_json"):
                    import json as _json
                    st.download_button("Download JSON", data=_json.dumps(rows, ensure_ascii=False, indent=2), file_name="testqueue_runs.json")
            with ec2:
                if st.button("Export CSV", key="cons_q_export_csv"):
                    import csv, io
                    if rows:
                        buf = io.StringIO()
                        writer = csv.DictWriter(buf, fieldnames=sorted({k for r in rows for k in r.keys()}))
                        writer.writeheader()
                        for r in rows:
                            writer.writerow(r)
                        st.download_button("Download CSV", data=buf.getvalue(), file_name="testqueue_runs.csv")
            with ec3:
                if qs.get("last_id"):
                    from . import admin_devtools as _adm_dt
                    if st.button("Full Output", key="cons_q_full_output"):
                        full = _adm_dt.get_test_run_output(qs["last_id"])
                        if full:
                            st.code(full["stdout"] or "(empty)")
                            if full.get("stderr"):
                                st.code(full["stderr"], language="text")
                            st.caption(full.get("note",""))
                    if st.button("Retry Last", key="cons_q_retry_last"):
                        new_id = _adm_dt.retry_test_run(qs["last_id"])
                        if new_id:
                            qs["last_id"] = new_id
                    if st.button("Last JSON", key="cons_q_last_json"):
                        import json as _json
                        rid = qs["last_id"]
                        st.download_button(
                            "Download Last JSON",
                            data=_json.dumps(_adm_dt.get_test_run(rid), ensure_ascii=False, indent=2),
                            file_name=f"testqueue_run_{rid}.json",
                        )
        if qs.get("last_id"):
            st.caption(f"Letzte Run ID: {qs['last_id']} | Status: {_adm_dt.get_test_run(qs['last_id'])['status'] if _adm_dt.get_test_run(qs['last_id']) else 'n/a'}")

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

with tabs[5]:
    st.subheader("DecisionCards")
    if not decision_cards_enabled:
        st.info("DecisionCards disabled (VEK_DECISIONCARDS=0)")
    else:
        from app.core.decision_card_repo import DecisionCardRepository
        from app.core.decision_card import make_decision_card
        repo_dc = DecisionCardRepository()
        st.caption("Create & Review lightweight investment decision cards")
        with st.expander("Create New Card", expanded=False):
            with st.form("dc_form"):
                c1, c2 = st.columns(2)
                card_id = c1.text_input("card_id", value=f"dc_{len(repo_dc.all())+1}")
                author = c2.text_input("author", value="me")
                title = st.text_input("title")
                # ... existing code continues (unchanged) ...

with tabs[6]:
    st.subheader("Investment Workbench Übersicht (Roadmap Preview)")
    st.caption("Feature-Matrix & Health Panels – Backend für einige zukünftige Features noch Platzhalter.")
    import pandas as _pd
    feature_rows = [
        {"Feature":"Realized Metrics","Status":"✅","Flag":"-","Backend":"metrics.aggregate_metrics","UI":"Analytics Tab"},
        {"Feature":"Unrealized Timeline (Aggregate)","Status":"✅","Flag":"mark_prices JSON","Backend":"unrealized_equity_timeline","UI":"Analytics Overlay"},
        {"Feature":"Unrealized Timeline (Per Ticker)","Status":"✅","Flag":"mark_prices JSON","Backend":"unrealized_equity_timeline_by_ticker","UI":"Workbench"},
        {"Feature":"Return Distribution","Status":"✅ (flag)","Flag":"VEK_ANALYTICS_EXT","Backend":"patterns.return_distribution","UI":"Analytics Extended"},
        {"Feature":"Holding Duration Stats","Status":"✅","Flag":"VEK_PATTERNS","Backend":"patterns.holding_duration_histogram","UI":"Analytics"},
        {"Feature":"Position Size / Exposure","Status":"✅ (flag)","Flag":"VEK_ANALYTICS_EXT","Backend":"metrics.position_size_series","UI":"Analytics Extended"},
        {"Feature":"Queue Aggregate Metrics","Status":"✅","Flag":"-","Backend":"testqueue.aggregate_metrics","UI":"DevTools / Workbench"},
        {"Feature":"Queue Persistence Health","Status":"✅","Flag":"-","Backend":"testqueue.get_persistence_stats","UI":"Workbench"},
        {"Feature":"Snapshots (Regression)","Status":"✅ (basic)","Flag":"-","Backend":"devtools.snapshot","UI":"DevTools"},
        {"Feature":"Decision Cards","Status":"✅","Flag":"VEK_DECISIONCARDS","Backend":"decision_card_repo","UI":"DecisionCards"},
        {"Feature":"Retrieval (Keyword)","Status":"✅ (basic)","Flag":"-","Backend":"retrieval.retrieve","UI":"Retrieval"},
        {"Feature":"Strategy Backtest (Sim Walk)","Status":"✅ (MVP)","Flag":"-","Backend":"sim.simple_walk","UI":"Simulation"},
        {"Feature":"Pro-Ticker Metrics","Status":"Planned","Flag":"(future)","Backend":"(to design)","UI":"Workbench"},
        {"Feature":"Risk Buckets / VaR","Status":"Planned","Flag":"(future)","Backend":"(to design)","UI":"Workbench"},
        {"Feature":"Alpha Factor Attribution","Status":"Planned","Flag":"(future)","Backend":"(to design)","UI":"Workbench"},
        {"Feature":"Scenario Engine","Status":"Planned","Flag":"(future)","Backend":"(to design)","UI":"Workbench"},
    ]
    st.dataframe(_pd.DataFrame(feature_rows))
    st.markdown("---")
    # Per-Ticker Unrealized Visualization
    st.subheader("Per-Ticker Unrealized (aktuelle Marks)")
    mp_text2 = st.text_area("Mark Prices JSON (für Per-Ticker)", value="", height=80, key="wb_marks")
    marks2 = {}
    if mp_text2.strip():
        try:
            marks2 = json.loads(mp_text2)
            if not isinstance(marks2, dict):
                st.warning("Marks JSON muss Objekt sein")
                marks2 = {}
        except Exception as e:
            st.error(f"JSON Fehler: {e}")
    if marks2 and repo.all():
        from app.analytics.metrics import unrealized_equity_timeline_by_ticker as _u_by_t
        per = _u_by_t(repo.all(), marks2)
        if per:
            import pandas as pd
            frames = []
            for ticker, series in per.items():
                dfp = pd.DataFrame(series, columns=["ts","unrealized"])  # type: ignore
                dfp["ticker"] = ticker
                frames.append(dfp)
            if frames:
                big = pd.concat(frames).set_index("ts")
                st.line_chart(big.pivot(columns="ticker", values="unrealized"))
        else:
            st.info("Keine offenen Positionen oder keine gültigen Marks.")
    else:
        st.caption("Gib Mark Prices als JSON ein um Pro-Ticker unrealized zu sehen.")
    st.markdown("---")
    # Queue Health
    st.subheader("Queue Health & Persistence")
    try:
        from app.core import testqueue as _tq
        q_agg = _tq.aggregate_metrics(limit=50)
        q_persist = _tq.get_persistence_stats()
        colh1, colh2 = st.columns(2)
        with colh1:
            st.caption("Aggregate Runs (recent)")
            st.json(q_agg)
        with colh2:
            st.caption("Persistence Stats")
            st.json(q_persist)
    except Exception as e:
        st.error(f"Queue Health Fehler: {e}")
    st.markdown("---")
    st.subheader("Zukunft Side-Bar (Mock)")
    st.markdown("""
    Geplante Erweiterungen:
    - Pro-Ticker Performance Attribution (Realized vs Benchmark)
    - Risiko-Kennzahlen (Rolling Volatility, Max Intraday Drawdown, VaR Approximator)
    - Faktor / Alpha Drivers (Correlation vs Momentum, Mean-Reversion, Seasonality)
    - Szenario Simulation (What-If Price Shocks, Slippage Modelle)
    - Portfolio Konstruktion (Optimierung, Rebalancing Vorschläge)
    - Alerts & Regeln (Threshold Breaches, Auto-Snapshots)
    - Data Ingestion Layer (Broker CSV Imports, API Connectors) — Flag-basiert abschaltbar
    """)

st.caption("Frontend-first Konsole • Personal Use • KISS")