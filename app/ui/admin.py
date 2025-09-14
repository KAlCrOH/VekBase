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

# --- DevTools (Increment: prompt3_roadmap_implement Increment A) ---
devtools_flag = bool(int(os.environ.get("VEK_ADMIN_DEVTOOLS", "1")))
if devtools_flag:
    from app.ui import admin_devtools as _adm_dt  # absolute import for script execution
    st.markdown("---")
    st.subheader("DevTools (Light)")
    if "adm_dt_state" not in st.session_state:
        st.session_state.adm_dt_state = {"filter": "", "last": None, "lint": None}
    s = st.session_state.adm_dt_state
    col_t1, col_t2 = st.columns([3,1])
    with col_t1:
        s["filter"] = st.text_input("Pytest -k Filter (optional)", s["filter"], key="adm_dt_filter")
    with col_t2:
        if st.button("Run Tests", key="adm_dt_run"):
            with st.spinner("Running tests..."):
                s["last"] = _adm_dt.run_test_subset(k_expr=s["filter"].strip() or None)
    if s.get("last"):
        last = s["last"]
        st.markdown(f"Status: **{last['status']}** | ✅ {last['passed']} / ❌ {last['failed']}")
        with st.expander("Test Output", expanded=False):
            st.code(last["stdout"] or "(empty)")
        if last.get("stderr"):
            with st.expander("Errors/Stderr"):
                st.code(last["stderr"])
    # Queued Test Runner (Increment G phase 1)
    with st.expander("Queued Test Runner", expanded=False):
        if "adm_queue" not in st.session_state:
            st.session_state.adm_queue = {"filter": "metrics", "runs": [], "last_id": None, "auto": True, "interval": 5, "last_poll": 0.0}
        q = st.session_state.adm_queue
        qc1, qc2, qc3, qc4, qc5 = st.columns([3,1,1,1,1])
        with qc1:
            q["filter"] = st.text_input("Queue -k Filter", q["filter"], key="adm_dt_qfilter")
        with qc2:
            if st.button("Queue Run", key="adm_dt_queue_submit"):
                from app.ui import admin_devtools as _adm_dt
                q["last_id"] = _adm_dt.submit_test_run(k_expr=q["filter"].strip() or None)
        with qc3:
            q["auto"] = st.checkbox("Auto", value=q.get("auto", True), help="Auto alle n Sekunden")
        with qc4:
            q["interval"] = st.number_input("Interval s", min_value=2, max_value=60, value=int(q.get("interval",5)), step=1, key="adm_dt_qint")
        with qc5:
            q["status_filter"] = st.multiselect("Status", ["queued","running","passed","failed","error"], default=q.get("status_filter",[]))
        q["show_persisted"] = st.checkbox("Persisted", value=q.get("show_persisted", True), help="Include JSONL history")
        # Manual refresh button
        if st.button("Refresh Now", key="adm_dt_queue_refresh"):
            from app.ui import admin_devtools as _adm_dt
            q["runs"] = _adm_dt.list_test_runs(limit=25, status=q.get("status_filter") or None, include_persisted=q.get("show_persisted", True))
            q["last_poll"] = _time.time()
        # Auto refresh tick
        import time as _time
        now = _time.time()
        if q.get("auto") and (now - q.get("last_poll",0) >= q.get("interval",5)):
            from app.ui import admin_devtools as _adm_dt
            q["runs"] = _adm_dt.list_test_runs(limit=25, status=q.get("status_filter") or None, include_persisted=q.get("show_persisted", True))
            q["last_poll"] = now
            # Rerun hint (Streamlit will rerun automatically after widget interactions)
        if q.get("runs"):
            # Add derived column duration_s if not present
            rows = q["runs"]
            try:
                import pandas as pd
                df = pd.DataFrame(rows)
                # Show key columns subset if large
                display_cols = [c for c in ["run_id","status","passed","failed","duration_s","queued_at","started_at","finished_at","stdout_truncated","stderr_truncated"] if c in df.columns]
                st.dataframe(df[display_cols])
            except Exception:
                st.json(rows)
            # Aggregate metrics (new increment)
            try:
                from app.ui import admin_devtools as _adm_dt
                ag = _adm_dt.get_queue_aggregates()
                if ag.get("total_runs",0) > 0:
                    st.caption(f"Aggregates: total={ag['total_runs']} pass_rate={ag['pass_rate']:.2f} fail_rate={ag['fail_rate']:.2f} error_rate={ag['error_rate']:.2f} mean_dur={ag['mean_duration_s'] if ag['mean_duration_s'] is not None else 'n/a'}s")
                else:
                    st.caption("Aggregates: (keine finished runs)")
            except Exception as _e:
                st.caption(f"Aggregates unavailable: {_e}")
            exp_c1, exp_c2, exp_c3 = st.columns([1,1,1])
            with exp_c1:
                if st.button("Export JSON", key="adm_dt_queue_export_json"):
                    import json as _json
                    st.download_button("Download JSON", data=_json.dumps(rows, ensure_ascii=False, indent=2), file_name="testqueue_runs.json")
            with exp_c2:
                if st.button("Export CSV", key="adm_dt_queue_export_csv"):
                    import csv, io
                    if rows:
                        buf = io.StringIO()
                        writer = csv.DictWriter(buf, fieldnames=sorted({k for r in rows for k in r.keys()}))
                        writer.writeheader()
                        for r in rows:
                            writer.writerow(r)
                        st.download_button("Download CSV", data=buf.getvalue(), file_name="testqueue_runs.csv")
            with exp_c3:
                if q.get("last_id"):
                    from app.ui import admin_devtools as _adm_dt
                    if st.button("Full Output", key="adm_dt_full_output"):
                        full = _adm_dt.get_test_run_output(q["last_id"])
                        if full:
                            st.code(full["stdout"] or "(empty)")
                            if full.get("stderr"):
                                st.code(full["stderr"], language="text")
                            st.caption(full.get("note",""))
                    if st.button("Retry Last", key="adm_dt_retry_last"):
                        new_id = _adm_dt.retry_test_run(q["last_id"])
                        if new_id:
                            q["last_id"] = new_id
                    # Single Run Export
                    if st.button("Last JSON", key="adm_dt_last_json"):
                        import json as _json
                        rid = q["last_id"]
                        st.download_button(
                            "Download Last JSON",
                            data=_json.dumps(_adm_dt.get_test_run(rid), ensure_ascii=False, indent=2),
                            file_name=f"testqueue_run_{rid}.json",
                        )
        if q.get("last_id"):
            from app.ui import admin_devtools as _adm_dt
            st.caption(f"Letzte Run ID: {q['last_id']} | Status: {_adm_dt.get_test_run(q['last_id'])['status'] if _adm_dt.get_test_run(q['last_id']) else 'n/a'}")
    # Lint
    col_l1, col_l2 = st.columns([1,4])
    with col_l1:
        if st.button("Run Lint", key="adm_dt_lint"):
            with st.spinner("Linting..."):
                s["lint"] = _adm_dt.run_lint_report()
    with col_l2:
        st.caption("Syntax + whitespace + mixed indent")
    if s.get("lint"):
        rep = s["lint"]
        st.markdown(f"Issues: {rep['total']} (Errors: {rep['errors']} / Warnings: {rep['warnings']})")
        if rep['issues']:
            import pandas as pd
            st.dataframe(pd.DataFrame(rep['issues']))
    # Benchmark Panel (Increment B)
    st.markdown("---")
    st.subheader("Benchmarks")
    if "adm_bench" not in st.session_state:
        st.session_state.adm_bench = {"target": None, "repeat": 3, "result": None}
    b = st.session_state.adm_bench
    reg = _adm_dt.list_benchmarks()
    if not b["target"] or b["target"] not in reg:
        b["target"] = next(iter(reg.keys())) if reg else None
    if reg:
        col_b1, col_b2, col_b3 = st.columns([2,1,1])
        with col_b1:
            b["target"] = st.selectbox("Target", list(reg.keys()), index=list(reg.keys()).index(b["target"]))
        with col_b2:
            b["repeat"] = st.number_input("Repeat", min_value=1, max_value=20, value=b["repeat"], step=1)
        with col_b3:
            if st.button("Run Benchmark", key="adm_dt_bench"):
                try:
                    with st.spinner("Benchmark running..."):
                        b["result"] = _adm_dt.run_benchmark(b["target"], repeat=int(b["repeat"]))
                except Exception as e:
                    b["result"] = {"error": str(e)}
        if b.get("result"):
            st.json(b["result"])
    else:
        st.info("No benchmarks registered.")
    # Snapshot Panel (Increment C)
    st.markdown("---")
    st.subheader("Snapshots")
    if "adm_snap" not in st.session_state:
        st.session_state.adm_snap = {"target": "metrics", "update": False, "result": None}
    sn = st.session_state.adm_snap
    targets = _adm_dt.list_snapshot_targets()
    c_s1, c_s2, c_s3 = st.columns([2,1,1])
    with c_s1:
        sn["target"] = st.selectbox("Target", targets, index=targets.index(sn["target"]) if sn["target"] in targets else 0)
    with c_s2:
        sn["update"] = st.checkbox("Update Baseline if Diff", value=sn["update"])
    with c_s3:
        if st.button("Run Snapshot", key="adm_dt_snap"):
            try:
                with st.spinner("Snapshot running..."):
                    sn["result"] = _adm_dt.run_snapshot(sn["target"], update=sn["update"])
            except Exception as e:
                sn["result"] = {"error": str(e)}
    if sn.get("result"):
        res = sn["result"]
        # Show high-level summary if available
        summary = res.get("summary") if isinstance(res, dict) else None
        if summary:
            st.markdown(
                f"Status: **{summary['status']}** | Diff Count: {summary['diff_count']} | Updated: {summary['updated']}"
            )
        st.json(res)
        nd = res.get("numeric_deltas") if isinstance(res, dict) else None
        if nd:
            try:
                import pandas as pd
                st.markdown("**Numeric Deltas**")
                st.dataframe(pd.DataFrame(nd))
            except Exception:
                st.caption("(numeric deltas table unavailable)")
    # Retrieval Panel (Increment D)
    st.markdown("---")
    st.subheader("Retrieval (Context)")
    retrieval_flag = bool(int(os.environ.get("VEK_RETRIEVAL", "1")))
    if retrieval_flag:
        from app.ui import admin_feature_wrappers as _feat
        if "adm_retr" not in st.session_state:
            st.session_state.adm_retr = {"query": "projekt", "limit": 3, "ticker": "", "as_of": "", "results": []}
        r = st.session_state.adm_retr
        c_rt1, c_rt2, c_rt3, c_rt4 = st.columns([2,1,1,1])
        with c_rt1:
            r["query"] = st.text_input("Query", r["query"])
        with c_rt2:
            r["limit"] = st.number_input("Limit", min_value=1, max_value=10, value=r["limit"], step=1)
        with c_rt3:
            r["ticker"] = st.text_input("Ticker", r["ticker"])
        with c_rt4:
            r["as_of"] = st.text_input("as_of (YYYY-MM-DD)", r["as_of"])
        if st.button("Search", key="adm_dt_retr"):
            r["results"] = _feat.retrieve_context(r["query"], limit=int(r["limit"]), ticker=(r["ticker"].strip() or None), as_of=(r["as_of"].strip() or None))
        if r["results"]:
            import pandas as pd
            st.dataframe(r["results"])
        else:
            st.caption("Keine Treffer oder noch keine Suche.")
    else:
        st.info("Retrieval disabled (VEK_RETRIEVAL=0)")
    # DecisionCards Panel (Increment D)
    st.markdown("---")
    st.subheader("DecisionCards")
    dc_flag = bool(int(os.environ.get("VEK_DECISIONCARDS", "1")))
    if dc_flag:
        from app.ui import admin_feature_wrappers as _feat
        if "adm_dc" not in st.session_state:
            st.session_state.adm_dc = {"list": [], "card": {"title": "", "author": "me", "id": "dc_admin_1"}}
        dcs = st.session_state.adm_dc
        c_dc1, c_dc2, c_dc3 = st.columns([2,1,1])
        with c_dc1:
            dcs["card"]["id"] = st.text_input("card_id", dcs["card"]["id"])
        with c_dc2:
            dcs["card"]["author"] = st.text_input("author", dcs["card"]["author"])
        with c_dc3:
            dcs["card"]["title"] = st.text_input("title", dcs["card"].get("title", ""))
        if st.button("Create Card", key="adm_dt_dc_create"):
            if dcs["card"]["title"].strip():
                try:
                    _feat.create_decision_card("data/decision_cards.json", card_id=dcs["card"]["id"], author=dcs["card"]["author"], title=dcs["card"]["title"], action={"type": "hold"})
                    dcs["list"] = _feat.list_decision_cards()
                except Exception as e:
                    st.error(f"Create failed: {e}")
        if st.button("Refresh", key="adm_dt_dc_refresh"):
            dcs["list"] = _feat.list_decision_cards()
        if dcs["list"]:
            import pandas as pd
            st.dataframe(dcs["list"])
        else:
            st.caption("Keine DecisionCards.")
    else:
        st.info("DecisionCards disabled (VEK_DECISIONCARDS=0)")
else:
    st.caption("DevTools disabled via VEK_ADMIN_DEVTOOLS=0")

st.caption("Personal tool. No enterprise features. ")
