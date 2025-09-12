# UI Console Spec (Frontend-First Streamlit)

Unified Konsole: `app/ui/console.py` (Tabs: Trades, Analytics, Simulation, DevTools).

Sections (Soll / Ist):
1) Trades: Tabelle (IST), Formular (IST), Import-Validierung (IST), Speichern/Export (IST)
2) Analytics: REALIZED PnL, Win-Rate, Profit-Factor, realized MaxDD, Holding-Dauer avg, realized Equity Curve, CAGR (IST). Unrealized PnL (teilweise Overlay), Patterns (IST via Feature Flag VEK_PATTERNS)
3) Patterns: Histogramme Holding-Dauer, Scatter Entry vs Return (IST in Analytics Tab, hinter VEK_PATTERNS)
4) Simulation: Parameter (basic: steps, seed, momentum window) + Persistenz data/results/<ts>_<hash>/ (IST); Erweiterte Parameter (TP/SL/Kosten) (offen). UI Mismatch: Erfolgsmeldung erwartet folder-Key im Result (Backlog P0)
5) DevTools: Pytest Runner (Filter, Status, Logs) (IST) + Lint/Benchmark (offen)
6) Retrieval/DecisionCards: Backend Stubs vorhanden, UI Panel (offen)
7) Live Quotes (optional): offen

Persistenz: meta.json (Parameter, Hash, final_cash) + equity.csv (Zeilen: ts,equity).

Backlog: UI SimResult Rückgabemismatch (#1) ERLEDIGT, DecisionCard/Retrieval Panels (#10) offen — siehe tmp_backlogCollection.md
Backlog (Analytics Bezug): CAGR (#6) ERLEDIGT, Unrealized Equity Curve (#7), Pattern Analytics (#8) — siehe tmp_backlogCollection.md
