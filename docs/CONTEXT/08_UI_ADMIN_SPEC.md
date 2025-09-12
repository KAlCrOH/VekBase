# UI Console Spec (Frontend-First Streamlit)

Unified Konsole: `app/ui/console.py` (Tabs: Trades, Analytics, Simulation, DevTools).

Sections (Soll / Ist):
1) Trades: Tabelle (IST), Formular (IST), Import-Validierung (IST), Speichern/Export (IST)
2) Analytics: REALIZED PnL, Win-Rate, Profit-Factor, realized MaxDD, Holding-Dauer avg, realized Equity Curve, CAGR (IST). Unrealized PnL (teilweise Overlay), Patterns (IST via Feature Flag VEK_PATTERNS)
3) Patterns: Histogramme Holding-Dauer, Scatter Entry vs Return (IST in Analytics Tab, hinter VEK_PATTERNS)
4) Simulation: Parameter (basic: steps, seed, momentum window) + Persistenz data/results/<ts>_<hash>/ (IST); Erweiterte Parameter (TP/SL/Kosten) (offen). UI Mismatch: Erfolgsmeldung erwartet folder-Key im Result (Backlog P0)
5) DevTools: Pytest Runner (Filter, Status, Logs) (IST) + Lint (Increment A) + Benchmarks (Increment B) + Snapshots (Increment C)
6) Retrieval/DecisionCards: Backend Stubs vorhanden, UI Panel (offen)
7) Live Quotes (optional): offen

Persistenz: meta.json (Parameter, Hash, final_cash) + equity.csv (Zeilen: ts,equity).

Backlog: UI SimResult Rückgabemismatch (#1) ERLEDIGT, DecisionCard/Retrieval Panels (#10) offen — siehe tmp_backlogCollection.md

Increment A (prompt3_roadmap_implement):
- Admin UI DevTools Sektion (Feature Flag `VEK_ADMIN_DEVTOOLS`, default=1)
- Funktionen: Test Run (optional -k Filter) + Lint Report Anzeige
- Keine neuen Dependencies / reine Nutzung core.devtools & core.linttools

Increment B:
- Benchmarks Panel (Target Auswahl, Repeat, Ergebnis JSON)
- Reuse core.benchtools (persist baseline unter data/devtools)
- Negative Case (invalid target) führt zu UI Fehlermeldung / ValueError Test

Increment C:
- Snapshot Panel (Target metrics|equity_curve, Update Toggle)
- Nutzung core.snapshots.ensure_and_diff (Baseline Anlage / Diff / Update)
- Tests für gültigen Lauf (metrics) + invalid target

Increment D:
- Retrieval Panel (Query, Limit, Ticker, as_of)
- DecisionCards Panel (Create + List, minimal Felder)
- Wrapper Modul admin_feature_wrappers (retrieve_context, list/create DecisionCard)
- Tests: retrieval smoke + decision card create/list

Increment E:
- Gemeinsames devtools_shared Wrapper Modul (Tests, Lint, Benchmarks, Snapshots)
- Console refactored to use shared wrappers (reduces duplicate core.* imports)
- Tests für Wrapper (Smoke, negative invalid nodeid)

Increment F:
- Snapshot Panel Erweiterung: Summary Anzeige (Status, Diff Count, Updated Flag)
- Numeric Deltas Tabelle für reine numerische Änderungen (Pfad, baseline, current, delta, delta_pct)
- Non-Breaking: Original JSON (status,diff,snapshot) bleibt unverändert nutzbar; neue Keys summary, numeric_deltas
- Tests erweitert (test_devtools_shared) zur Validierung von summary & numeric_deltas Schema

Backlog (Analytics Bezug): CAGR (#6) ERLEDIGT, Unrealized Equity Curve (#7), Pattern Analytics (#8) — siehe tmp_backlogCollection.md
