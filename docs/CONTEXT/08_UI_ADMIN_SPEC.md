# UI Console Spec (Frontend-First Streamlit)

Unified Konsole: `app/ui/console.py` (Tabs: Trades, Analytics, Simulation, DevTools).

Sections (Soll / Ist):
1) Trades: Tabelle (IST), Formular (IST), Import-Validierung (IST), Speichern/Export (IST)
2) Analytics: realized/unrealized PnL, Win-Rate, Profit-Factor, realized MaxDD, Holding-Dauer avg, realized Equity Curve (IST); CAGR, Patterns (offen)
3) Patterns: Histogramme Holding-Dauer, Scatter Entry vs Return (offen)
4) Simulation: Parameter (basic: steps, seed, momentum window) + Persistenz data/results/<ts>_<hash>/ (IST); Erweiterte Parameter (TP/SL/Kosten) (offen)
5) DevTools: Pytest Runner (IST) + Lint/Benchmark (offen)
6) Retrieval/DecisionCards: Backend Stubs vorhanden, UI Panel (offen)
7) Live Quotes (optional): offen

Persistenz: meta.json (Parameter, Hash, final_cash) + equity.csv (Zeilen: ts,equity).
