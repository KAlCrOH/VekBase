# UI Console Spec (Investor-Focused Streamlit) – Redesign

Unified Konsole: `app/ui/console.py` (Tabs: Trades, Analytics, Simulation, Retrieval, DecisionCards, Workbench). DevTools / Test / Lint / Benchmark / Snapshot Panels wurden entfernt (Redesign Fokus: Investor Value, Klarheit, geringere kognitive Last).

Sections (Soll / Ist):
1) Trades: Tabelle (IST), Formular (IST), Import-Validierung (IST), Speichern/Export (IST)
2) Analytics: REALIZED PnL, Win-Rate, Profit-Factor, realized MaxDD, Holding-Dauer avg, realized Equity Curve, CAGR (IST). Unrealized PnL (Overlay), Patterns (Histogram/Scatter, Flag `VEK_PATTERNS`). Risk Metrics (VaR/ES/Rolling VaR – Flag `VEK_RISK_METRICS`).
3) Patterns: Histogramme Holding-Dauer, Scatter Entry vs Return (IST in Analytics Tab, hinter VEK_PATTERNS)
4) Simulation: Parameter (basic: steps, seed, momentum window) + Persistenz data/results/<ts>_<hash>/ (IST); Erweiterte Parameter (TP/SL/Kosten) (IMPLEMENTIERT). UI Persistenz: Hash & Zeitstempel anzeigen (Nice-to-have: Link Button). 
5) (entfernt) – Ehemalige DevTools/Test Funktionen (Pytest Runner, Lint, Benchmarks, Snapshots, Test Queue) sind aus der UI entfernt und verbleiben nur als Backend-Utilities für interne Wartung.
6) Retrieval/DecisionCards: Retrieval Panel (Query, Limit) Basic+Advanced+Embedding (Flags `VEK_RETRIEVAL_ADV`, `VEK_RETRIEVAL_EMB`). DecisionCard Panel (Create/List) – Workflow Status & Reviewer Anzeige (Review / Approve / Reject Buttons geplante Erweiterung). Expiry Indikator (wenn `expires_at` < now rot / warnend).
7) Live Quotes (optional): offen
8) Theming: Dark Mode (Flag `VEK_CONSOLE_DARK`) – invertierte Farbpalette für Charts (Hintergrund #1e1e1e, angepasste Axis/Label Farben).
9) Planned Visualization Extensions:
	- Regime Overlay: Farbband auf Equity Curve (Flag `VEK_REGIME`).
	- Portfolio Allocation: Stapel-Flächenchart für Kapitalanteil je Strategie (Flag `VEK_PORTFOLIO`).
	- Failure Clusters: Bar/Scatter mit Cluster Loss Contribution (Flag `VEK_FAILURE_MINER`).

Persistenz: meta.json (Parameter, Hash, final_cash) + equity.csv (Zeilen: ts,equity).

Backlog (UI Fokus):
- DecisionCard Workflow Actions (approve/reject inline) + Audit Trail Modal.
- Retrieval Filter Controls (ticker, as_of) + Regime Filter (nach Implementierung Regime Labeling).
- Strategy Batch Runner Dashboard (grid results: param→metric heatmap, robustness summary).
- Portfolio Optimizer Panel (policy selection, correlation matrix mini-heatmap).
- Failure Pattern Miner Panel (cluster table + narrative preview).
- Snapshot Numeric Diff UI Enhancements (highlight thresholds, toggle epsilon grouping).

Historische DevTools Inkremente (A–J) wurden obsolet gemacht. Kern-Funktionen (Lint, Benchmarks, Snapshots, Test Queue) verbleiben im Code (Backend) für interne Qualitätssicherung, sind jedoch nicht mehr Bestandteil der Investor UI. Feature Flags `VEK_ADMIN_DEVTOOLS` und `VEK_TEST_CENTER` sind de-facto deprecated (keine UI Wirkung).

Aktueller Fokus (Investor Roadmap Extract):
- Data Ingestion & Trade Import UX (CSV Mapping, Validierungsreport)
- Erweiterte Analytics (Risk Buckets, Rolling Vol, Exposure Timeline)
- Strategy Batch Auswertung (Robustness Summary in Workbench Tab)
- Portfolio / Factor Attribution (frühe Prototyp Metriken)
- DecisionCard Workflow (Review / Approve Actions + Audit Trail)
- Retrieval Erweiterung (Regime Filter, semantische Layer optional)

Cleanup Notes:
- Entfernte UI Komponenten: Pytest Runner, Lint Panel, Benchmarks Panel, Snapshot Panel, Queued Test Runner, Queue Health.
- Entfernte Tests: test_test_center_panel, test_test_center_artifacts (UI-spezifisch).
- Backend Module belassen für Wartung: `app/ui/admin_devtools.py`, `app/ui/devtools_shared.py` (können später in internen Namespace verschoben werden).

Nächste Schritte (Proposed Next Increments):
1. Trade Import Enhancements (Schema Detection + Preview Diffs)
2. Risk Metrics Mini-Panel (Rolling Volatility + Max Drawdown Trend)
3. Strategy Batch Result Heatmap (param vs CAGR) + Export
4. DecisionCard Review Actions + Status Timeline
5. Portfolio Exposure Timeline (gestapelte Flächen je Ticker/Strategy)

Diese Datei bildet nun ausschließlich investorenrelevante UI Aspekte ab.
