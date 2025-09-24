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
    # --- Import Assistant (Schema Detect & Diff Preview) ---
    st.markdown("---")
    with st.expander("Import Assistant (CSV Schema & Diff)", expanded=False):
        from app.core.trade_import import infer_csv_schema, parse_csv_text, diff_trades
        mode = st.radio("Quelle", ["Paste CSV", "Upload File"], horizontal=True, key="imp_mode")
        csv_text = ""
        upload_rows = []
        if mode == "Paste CSV":
            csv_text = st.text_area("CSV Text", height=160, placeholder="trade_id,ts,ticker,action,shares,price,fees\n...")
            rows = parse_csv_text(csv_text) if csv_text.strip() else []
        else:
            up = st.file_uploader("CSV Datei", type=["csv"], accept_multiple_files=False)
            if up is not None:
                try:
                    csv_text = up.read().decode("utf-8")
                except Exception as e:
                    st.error(f"Decode Fehler: {e}")
                rows = parse_csv_text(csv_text) if csv_text else []
            else:
                rows = []
        # Schema inference
        if csv_text.strip():
            schema = infer_csv_schema(csv_text)
            sc1, sc2 = st.columns([2,1])
            with sc1:
                st.caption("Schema Resultat")
                st.json({k: schema[k] for k in ["header","required_missing","unexpected","row_count","valid"]})
            with sc2:
                if schema.get("issues"):
                    st.caption("Schema Issues")
                    for iss in schema["issues"]:
                        st.warning(iss)
            # Diff vs existing repo
            if rows:
                diff = diff_trades(repo.all(), rows)
                st.caption("Diff Zusammenfassung")
                st.json({k: diff[k] for k in ["candidate_count","importable_count"]})
                col_d1, col_d2, col_d3 = st.columns(3)
                with col_d1:
                    st.caption("Neue Trades")
                    st.code("\n".join(diff["new_ids"]) or "(none)")
                with col_d2:
                    st.caption("Geändert (trade_id)")
                    st.code("\n".join(diff["changed"]) or "(none)")
                with col_d3:
                    st.caption("Duplikate")
                    st.code("\n".join(diff["duplicate_ids"]) or "(none)")
                if diff.get("issues"):
                    st.caption("Import Issues")
                    for iss in diff["issues"][:20]:
                        st.info(iss)
                # Apply import (only new, valid)
                if diff.get("new_ids") and st.button(f"Importiere {diff['importable_count']} neue Trades", key="do_import_trades"):
                    from app.core.trade_model import validate_trade_dict, TradeValidationError
                    added = 0
                    for r in rows:
                        if str(r.get("trade_id")) in diff["new_ids"]:
                            try:
                                repo.add_trade(validate_trade_dict(r))
                                added += 1
                            except TradeValidationError as e:
                                st.error(f"Fehler bei {r.get('trade_id')}: {e}")
                    if added:
                        try:
                            repo.export_csv(trades_path)
                        except Exception:
                            pass
                        st.success(f"{added} Trades importiert & gespeichert.")
                        st.experimental_rerun()
        else:
            st.caption("Füge CSV Text ein oder lade eine Datei hoch, um Schema zu prüfen.")

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
                # Regime Overlay & Summary (Flag VEK_REGIME)
                if bool(int(os.environ.get("VEK_REGIME", "0"))):
                    try:
                        from app.ui.regime_ui import summarize_regimes, compute_overlay_segments
                        prices_series = list(full.sort_values("ts")["equity_realized"].dropna()) if "equity_realized" in full.columns else []
                        reg_payload = summarize_regimes(repo.all(), prices_series)
                        labels = reg_payload.get("labels") or []
                        if labels:
                            segs = compute_overlay_segments(labels)
                            if segs:
                                import pandas as pd
                                eq_only = full.sort_values("ts")[["ts","equity_realized"]].dropna()
                                def _idx_ts(i:int):
                                    return eq_only.iloc[min(i, len(eq_only)-1)]["ts"] if len(eq_only) else None
                                rows = [{
                                    "start_ts": _idx_ts(s['start_idx']),
                                    "end_ts": _idx_ts(s['end_idx']),
                                    "vol_bucket": s['vol_bucket'],
                                    "trend_bucket": s['trend_bucket'],
                                } for s in segs]
                                df_seg = pd.DataFrame(rows)
                                st.caption("Regime Segments (compressed)")
                                st.dataframe(df_seg.head(40))
                            summ = reg_payload.get("summary", {})
                            if summ.get("regimes"):
                                try:
                                    import pandas as pd
                                    df_reg = pd.DataFrame(summ['regimes'])
                                    st.caption("Regime Return Summary")
                                    st.dataframe(df_reg)
                                except Exception:
                                    st.json(summ)
                        else:
                            st.info("Nicht genug Daten für Regime (Flag aktiv)")
                    except Exception as e:
                        st.warning(f"Regime Overlay Fehler: {e}")
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
            # Portfolio Exposure Timeline (stacked by ticker) outside two-column layout to use full width
            with st.expander("Portfolio Exposure Timeline", expanded=False):
                trades = repo.all()
                if trades:
                    try:
                        import pandas as pd
                        # Build exposure per trade per ticker (using cumulative lot valuation at execution price)
                        rows = []
                        inventory: dict[str, list[tuple[float,float]]] = {}
                        for t in sorted(trades, key=lambda x: x.ts):
                            if t.action == "BUY":
                                inventory.setdefault(t.ticker, []).append((t.shares, t.price))
                            else:  # SELL
                                lots = inventory.get(t.ticker, [])
                                remaining = t.shares
                                i = 0
                                while remaining > 1e-12 and i < len(lots):
                                    lot_sh, lot_price = lots[i]
                                    take = min(lot_sh, remaining)
                                    lot_sh -= take
                                    remaining -= take
                                    if lot_sh <= 1e-12:
                                        lots.pop(i)
                                    else:
                                        lots[i] = (lot_sh, lot_price)
                                        i += 1
                            # compute per-ticker exposure snapshot after this trade
                            snap: dict[str,float] = {}
                            for tick, lots in inventory.items():
                                exp = 0.0
                                for lot_sh, lot_price in lots:
                                    exp += lot_sh * lot_price
                                if exp > 0:
                                    snap[tick] = round(exp, 6)
                            if snap:
                                snap["ts"] = t.ts
                                rows.append(snap)
                        if rows:
                            dfexp = pd.DataFrame(rows).fillna(0.0)
                            dfexp = dfexp.set_index("ts")
                            # Convert ts to string for Streamlit if needed
                            dfexp.index = dfexp.index.map(lambda x: x.isoformat() if hasattr(x, 'isoformat') else x)
                            st.caption("Stacked Gross Exposure by Ticker (execution price marked exposure)")
                            try:
                                import altair as alt
                                df_long = dfexp.reset_index().melt(id_vars=["ts"], var_name="ticker", value_name="exposure")
                                chart = alt.Chart(df_long).mark_area().encode(
                                    x=alt.X("ts:T", title="Timestamp"),
                                    y=alt.Y("exposure:Q", stack='normalize', title="Exposure (Normalized)"),
                                    color=alt.Color("ticker:N", legend=alt.Legend(title="Ticker")),
                                    tooltip=["ts","ticker","exposure"]
                                ).properties(height=240)
                                st.altair_chart(chart, use_container_width=True)
                                st.caption("Normalized stack (each area shows proportion of total gross exposure).")
                                # Absolute stacked variant
                                chart_abs = alt.Chart(df_long).mark_area().encode(
                                    x=alt.X("ts:T", title="Timestamp"),
                                    y=alt.Y("exposure:Q", stack='zero', title="Exposure (Absolute)"),
                                    color=alt.Color("ticker:N", legend=None),
                                    tooltip=["ts","ticker","exposure"]
                                ).properties(height=240)
                                st.altair_chart(chart_abs, use_container_width=True)
                            except Exception as _e_exp:
                                st.dataframe(dfexp)
                                st.caption(f"(Altair fallback: {_e_exp})")
                        else:
                            st.info("No exposure snapshots to display.")
                    except Exception as e:
                        st.warning(f"Exposure timeline error: {e}")
                else:
                    st.info("No trades loaded.")
        # --- Increment I2: Research Preview Panels (Attribution & Portfolio) ---
        try:
            from app.ui.research_preview import panels_enabled as _rp_enabled, attribution_preview as _attr_prev, portfolio_preview as _port_prev
            if _rp_enabled():
                st.markdown("---")
                st.subheader("Research Preview")
                eq_curve = realized_equity_curve(repo.all())
                # Attribution Panel (Flag VEK_ATTRIBUTION)
                if bool(int(os.environ.get("VEK_ATTRIBUTION","1"))):
                    with st.expander("Factor Attribution (Preview)", expanded=False):
                        payload = _attr_prev(eq_curve)
                        st.json({k:v for k,v in payload.items() if k != 'artifact_path'})
                        if payload.get('artifact_path'):
                            st.caption(f"Artifact: {payload['artifact_path']}")
                # Portfolio Panel (Flag VEK_PORTFOLIO)
                if bool(int(os.environ.get("VEK_PORTFOLIO","1"))):
                    with st.expander("Portfolio Optimizer (Preview)", expanded=False):
                        payload = _port_prev(eq_curve)
                        st.json({k:v for k,v in payload.items() if k != 'artifact_path'})
                        if payload.get('artifact_path'):
                            st.caption(f"Artifact: {payload['artifact_path']}")
        except Exception as _e_rp:
            st.caption(f"Research preview unavailable: {_e_rp}")
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
import os as _os

# --- Increment I2: Metrics Snapshot Widget (OPTIMAL) ---
try:
    # Heuristik: earliest tab likely main dashboard (tabs[0])
    with tabs[0]:  # type: ignore[name-defined]
        import streamlit as st  # already imported above in file (safe re-import)
        if 'metrics_snapshot_rendered' not in st.session_state:
            st.session_state.metrics_snapshot_rendered = True
            try:
                from app.core.trade_repo import TradeRepository  # type: ignore
                from app.analytics.metrics import aggregate_metrics  # type: ignore
                # Repo / data acquisition reused from existing console context; fallback simple load
                # We reuse or reconstruct a repo if variable not globally available
                repo_obj = None
                if 'repo' in globals():  # existing pattern in file
                    repo_obj = globals().get('repo')
                if repo_obj is None:
                    # minimal fallback (empty repo) – metrics widget handles empty
                    from app.core.trade_model import Trade  # type: ignore
                    repo_obj = TradeRepository()
                trades = getattr(repo_obj, 'all', lambda: [])()
                metrics = aggregate_metrics(trades) if trades else None
                st.markdown('### Metrics Snapshot')
                if not metrics:
                    st.caption('(no data)')
                else:
                    # Select subset & thresholds
                    subset_keys = ['total_realized_pnl','win_rate','max_drawdown_realized','avg_holding_duration_sec','trades_total']
                    thresholds = {
                        'win_rate': [(0.5,'red'), (0.6,'amber'), (0.7,'green')],
                        'total_realized_pnl': [(-1,'red'), (0,'amber'), (1,'green')],
                        'max_drawdown_realized': [( -1000000,'green'), (-100,'amber'), (-100000000,'red')],  # placeholder ordering by magnitude
                        'avg_holding_duration_sec': [(0,'green'), (3600*24,'amber'), (3600*24*7,'red')],
                        'trades_total': [(0,'red'), (5,'amber'), (10,'green')],
                    }
                    cols = st.columns(len(subset_keys))
                    for i,key in enumerate(subset_keys):
                        val = metrics.get(key,0)
                        color = 'grey'
                        if key in thresholds:
                            # Interpret thresholds ascending; pick first matching color by rule logic adaptation
                            tdefs = thresholds[key]
                            if key == 'win_rate':
                                color = 'red' if val < 0.5 else 'amber' if val < 0.7 else 'green'
                            elif key == 'total_realized_pnl':
                                color = 'red' if val < 0 else 'amber' if val < 100 else 'green'
                            elif key == 'max_drawdown_realized':
                                color = 'green' if val > -50 else 'amber' if val > -200 else 'red'
                            elif key == 'avg_holding_duration_sec':
                                color = 'green' if val < 3600*24 else 'amber' if val < 3600*24*7 else 'red'
                            elif key == 'trades_total':
                                color = 'red' if val < 1 else 'amber' if val < 10 else 'green'
                        with cols[i]:
                            st.markdown(f"<div style='text-align:center'><span style='font-size:0.8em'>{key}</span><br><span style='font-weight:bold;color:{color}'>"+ (f"{val:.2f}" if isinstance(val,float) else str(val)) + "</span></div>", unsafe_allow_html=True)
            except Exception as _e:
                st.caption(f"Metrics Snapshot unavailable: {_e}")
except Exception:
    # Silent fallback (do not break console if tabs structure differs)
    pass

# DevTools Tab (refactored to use app.core.devtools)
with tabs[3]:
    st.subheader("DevTools — Test Runner")
    if not devtools_enabled:
        st.info("DevTools deaktiviert (VEK_DEVTOOLS=0). Setze Env Var um zu aktivieren.")
    else:
        # --- Increment I1: Optional neues 'Test Center' Panel (Artefakte, Status, Logs) ---
        test_center_flag = bool(int(_os.environ.get("TEST_CENTER_FLAG", "1")))
        if test_center_flag:
            with st.expander("Test Center (Artifacts)", expanded=False):
                from app.ui import admin_devtools as _adm_dt
                if "tc_state" not in st.session_state:
                    st.session_state.tc_state = {"filter":"","module":"","last":None, "selected_run":None}
                tcs = st.session_state.tc_state
                ctc1, ctc2, ctc3, ctc4, ctc5 = st.columns([3,2,1,1,1])
                with ctc1:
                    tcs["filter"] = st.text_input("-k Filter", tcs["filter"], key="tc_filter")
                with ctc2:
                    tcs["module"] = st.text_input("Module Substr", tcs["module"], key="tc_module")
                with ctc3:
                    if st.button("Run", key="tc_run_btn"):
                        with st.spinner("Running (artifacts)..."):
                            tcs["last"] = _adm_dt.run_test_center(k_expr=tcs["filter"].strip() or None, module_substr=tcs["module"].strip() or None)
                with ctc4:
                    if st.button("Refresh", key="tc_refresh_btn"):
                        pass  # no-op triggers rerender to update history
                with ctc5:
                    if tcs.get("last"):
                        badge_color = {"passed":"green","failed":"red","error":"red"}.get(tcs["last"]["status"],"grey")
                        st.markdown(f"Status:<br><span style='color:{badge_color};font-weight:bold'>{tcs['last']['status']}</span>", unsafe_allow_html=True)
                # Detail view (selected or last)
                detail = tcs.get("selected_run") or tcs.get("last")
                if detail:
                    st.markdown(f"Run: {detail['run_id']} – ✅ {detail['passed']} / ❌ {detail['failed']}")
                    with st.expander("Stdout", expanded=False):
                        st.code(detail.get("stdout_truncated") or "(empty)")
                    if detail.get("stderr_truncated"):
                        with st.expander("Stderr", expanded=False):
                            st.code(detail["stderr_truncated"], language="text")
                    arts = detail.get("artifacts") or {}
                    if any(arts.values()):
                        import os as _os2
                        st.caption("Artifacts (click path to copy):")
                        for k,v in arts.items():
                            if v and _os2.path.exists(v):
                                st.code(f"{k}: {v}")
                # History Table
                runs = _adm_dt.list_test_center_runs(limit=10)
                if runs:
                    import pandas as _pd
                    df_hist = _pd.DataFrame([
                        {"run_id": r['run_id'], "status": r['status'], "passed": r['passed'], "failed": r['failed'], "junit": bool(r.get('artifacts',{}).get('junit')), "coverage": bool(r.get('artifacts',{}).get('coverage'))}
                        for r in runs
                    ])
                    st.markdown("#### Recent Runs")
                    st.dataframe(df_hist)
                    pick = st.selectbox("Select Run", ["(latest)"] + list(df_hist["run_id"].values), index=0)
                    if pick != "(latest)":
                        try:
                            tcs["selected_run"] = _adm_dt.get_test_center_run(pick)
                        except Exception as _e_pick:
                            st.warning(f"Lookup failed: {_e_pick}")
                    else:
                        tcs["selected_run"] = None
        if "dt_state" not in st.session_state:
            st.session_state.dt_state = {
                "status": "idle",  # idle|running|passed|failed|error
                "stdout": "",
                "stderr": "",
                "filter": "",
                "module": "",
                "collected": [],
                "selected": set(),
                "summary": None,
                "sections": ["stdout", "summary"],
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
            # Persist summary counts to session (robuster als flüchtige Variable 'res')
            s["summary"] = {"passed": res.get("passed", 0), "failed": res.get("failed", 0)}
            # Telemetry (Increment X3) – nur lokal bei Flag
            try:
                from app.ui import devtools_events as _dt_events
                _dt_events.emit("test_run", {"status": s["status"], **s["summary"], "selected": len(s.get("selected", []))})
                if s["status"] == "failed":
                    _dt_events.emit("test_run_failed", {"failed": s["summary"].get("failed", 0)})
            except Exception:
                # Hard-fail vermeiden; Telemetrie darf UI nicht stören
                pass
            # Session Log (Increment X4)
            try:
                from app.ui import devtools_session_log as _sess_log
                _sess_log.add_test_run({
                    "status": s["status"],
                    "passed": s["summary"]["passed"],
                    "failed": s["summary"]["failed"],
                    "selected": len(s.get("selected", [])),
                })
            except Exception:
                pass

        # --- Output Filter (Increment X2) ---
        output_filter_flag = bool(int(_os.environ.get("VEK_DEVTOOLS_OUTPUT_FILTER", "1")))
        if output_filter_flag:
            from app.ui.devtools_output_filter import filter_output_sections as _filter_out
            s["sections"] = st.multiselect(
                "Output Sections",
                options=["stdout", "stderr", "summary"],
                default=s.get("sections", ["stdout", "summary"]),
                help="Wähle welche Output-Sektionen angezeigt werden sollen",
                key="dt_sections_sel"
            ) or []
            data_map = {"stdout": s.get("stdout"), "stderr": s.get("stderr"), "summary": s.get("summary")}
            filtered = _filter_out(data_map, s["sections"])
            if not filtered:
                st.caption("(Keine Sektionen ausgewählt)")
            else:
                if "stdout" in filtered:
                    with st.expander("Test Output", expanded=True):
                        st.code(filtered["stdout"] or "(empty)")
                if "summary" in filtered and isinstance(filtered.get("summary"), dict):
                    summ = filtered["summary"]
                    st.markdown(f"**Summary:** ✅ {summ.get('passed',0)} | ❌ {summ.get('failed',0)}")
                if "stderr" in filtered and filtered.get("stderr"):
                    with st.expander("Errors/StdErr", expanded=False):
                        st.code(filtered["stderr"])
            # Audit Export Buttons (Increment X5)
            from app.ui import devtools_audit_export as _audit
            exp_col1, exp_col2 = st.columns([1,1])
            with exp_col1:
                if st.button("Export JSON (Last Run)"):
                    js = _audit.export_json(s)
                    if js:
                        st.download_button("Download JSON", data=js, file_name="last_test_run.json")
                    else:
                        st.info("Kein Testlauf vorhanden.")
            with exp_col2:
                if st.button("Export CSV (Last Run)"):
                    csv_txt = _audit.export_csv(s)
                    if csv_txt:
                        st.download_button("Download CSV", data=csv_txt, file_name="last_test_run.csv")
                    else:
                        st.info("Kein Testlauf vorhanden.")
        else:
            # Legacy Darstellung ohne Filter
            with st.expander("Test Output", expanded=True):
                st.code(s["stdout"] or "(empty)")
                if isinstance(s.get("summary"), dict):
                    st.markdown(f"**Summary:** ✅ {s['summary'].get('passed',0)} | ❌ {s['summary'].get('failed',0)}")
            if s.get("stderr"):
                with st.expander("Errors/StdErr"):
                    st.code(s["stderr"])
            # Audit Export (Legacy Mode)
            from app.ui import devtools_audit_export as _audit
            exp_l1, exp_l2 = st.columns([1,1])
            with exp_l1:
                if st.button("Export JSON (Last Run)", key="legacy_exp_json"):
                    js = _audit.export_json(s)
                    if js:
                        st.download_button("Download JSON", data=js, file_name="last_test_run.json")
                    else:
                        st.info("Kein Testlauf vorhanden.")
            with exp_l2:
                if st.button("Export CSV (Last Run)", key="legacy_exp_csv"):
                    csv_txt = _audit.export_csv(s)
                    if csv_txt:
                        st.download_button("Download CSV", data=csv_txt, file_name="last_test_run.csv")
                    else:
                        st.info("Kein Testlauf vorhanden.")
        # Session Log Panel (Increment X4)
        with st.expander("Session Test Runs", expanded=False):
            from app.ui import devtools_session_log as _sess_log
            # Filter UI
            sel_status = st.multiselect("Status Filter", ["passed","failed","error"], default=[])
            runs_view = _sess_log.list_test_runs(limit=25, status=sel_status or None)
            if runs_view:
                try:
                    import pandas as pd
                    df_runs = pd.DataFrame(runs_view)
                    df_runs = df_runs.sort_values("ts", ascending=False)
                    cols = [c for c in ["ts","status","passed","failed","selected"] if c in df_runs.columns]
                    st.dataframe(df_runs[cols])
                except Exception:
                    st.json(runs_view)
            else:
                st.caption("Keine Session Runs.")
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
            # Removed Snapshot Regression & Dev/Test Queue UI (investor-focused redesign)
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
        st.caption("(Snapshot / Test Queue Panels entfernt – Fokus auf Investor Features)")

        # Strategy Batch Panel (Flag-gated: VEK_STRAT_SWEEP)
        if bool(int(_os.environ.get("VEK_STRAT_SWEEP", "0"))):
            st.markdown("---")
            with st.expander("Strategy Batch (Robustness)", expanded=False):
                st.caption("Analyse Robustheit via Param Grid & Seeds — Flag VEK_STRAT_SWEEP=1 aktiv.")
                from app.ui.strategy_batch_ui import run_strategy_batch_ui as _sb_ui
                if "strat_batch_state" not in st.session_state:
                    st.session_state.strat_batch_state = {
                        "strategies": '["ma_crossover","random_flip"]',
                        "param_grid": '{"ma_short":[5,7],"ma_long":[15,20],"flip_prob":[0.05,0.1]}',
                        "seeds": '1,2',
                        "running": False,
                        "last": None,
                        "show_results": True,
                    }
                sb = st.session_state.strat_batch_state
                c1, c2 = st.columns([3,2])
                with c1:
                    sb["strategies"] = st.text_area("Strategies JSON", value=sb["strategies"], height=60,
                        help='List of strategy names (registry: ma_crossover, random_flip)')
                with c2:
                    sb["seeds"] = st.text_input("Seeds (CSV)", value=sb["seeds"], help="Comma separated integers")
                sb["param_grid"] = st.text_area("Param Grid JSON", value=sb["param_grid"], height=80,
                    help='JSON object mapping param->list. Irrelevant params ignored by strategies.')
                run_clicked = st.button("Run Strategy Batch", disabled=sb["running"], key="sb_run_btn")
                if run_clicked:
                    sb["running"] = True
                    with st.spinner("Running batch..."):
                        res = _sb_ui(sb["strategies"], sb["param_grid"], sb["seeds"], price_series=None)
                    sb["last"] = res
                    sb["running"] = False
                if sb.get("last"):
                    last = sb["last"]
                    if last.get("error"):
                        st.error(last["error"])
                    else:
                        summary = last.get("summary", {})
                        st.markdown("**Summary**")
                        st.json(summary)
                        if sb.get("show_results"):
                            rs = last.get("results") or []
                            if rs:
                                try:
                                    import pandas as _pd
                                    df = _pd.DataFrame([
                                        {
                                            "strategy": r["strategy"],
                                            "param_hash": r["param_hash"],
                                            "seed": r["seed"],
                                            "cagr": r["metrics"]["cagr"],
                                            "max_dd": r["metrics"]["max_drawdown_realized"],
                                        } for r in rs
                                    ])
                                    st.dataframe(df)
                                    # Heatmap (param_hash vs seed, aggregated mean CAGR per cell)
                                    try:
                                        import altair as alt
                                        heat_df = df.groupby(["param_hash","seed"], as_index=False)["cagr"].mean()
                                        from .console_theme import apply_console_theme
                                        heat_chart = alt.Chart(heat_df).mark_rect().encode(
                                            x=alt.X("param_hash:N", title="Param Hash"),
                                            y=alt.Y("seed:O", title="Seed"),
                                            color=alt.Color("cagr:Q", scale=alt.Scale(scheme="blues"), title="CAGR"),
                                            tooltip=["param_hash","seed","cagr"]
                                        ).properties(height=200)
                                        heat_chart = apply_console_theme(heat_chart)
                                        st.caption("CAGR Heatmap (Param Hash vs Seed)")
                                        st.altair_chart(heat_chart, use_container_width=True)
                                    except Exception as _e_hm:
                                        st.caption(f"(heatmap unavailable: {_e_hm})")
                                except Exception:
                                    st.caption("(results table unavailable)")
        else:
            st.caption("Strategy Batch Panel deaktiviert (VEK_STRAT_SWEEP=0).")

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
                description = st.text_area("description", height=60)
                c3, c4 = st.columns(2)
                ticker = c3.text_input("ticker (optional)").upper()
                as_of = c4.text_input("as_of (YYYY-MM-DD)", value=datetime.now().strftime("%Y-%m-%d"))
                long_term = st.checkbox("Long Term Holding", value=True, help="Mark as long-term investment")
                submitted_dc = st.form_submit_button("Create Decision Card")
                if submitted_dc:
                    with st.spinner("Saving card..."):
                        try:
                            card = make_decision_card(
                                card_id=card_id,
                                author=author,
                                title=title,
                                description=description,
                                ticker=ticker or None,
                                as_of=as_of or None,
                                long_term=long_term,
                            )
                            repo_dc.add(card)
                            st.success(f"Decision Card {card_id} created")
                        except Exception as e:
                            st.error(f"Error creating card: {e}")
        st.markdown("---")
        st.subheader("Existing Decision Cards")
        if repo_dc.all():
            for card in repo_dc.all():
                with st.expander(card.card_id, expanded=False):
                    st.json(card.to_dict())
        else:
            st.info("No decision cards found. Create a new card using the form above.")

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
    # Removed Dev/Test oriented rows (Queue metrics, Snapshots) in investor-focused view
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
    # Queue Health removed (Dev/Test scope)
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