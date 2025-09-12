# UI Admin Spec (Streamlit)

Sections (Soll / Ist):
1) Trades: Tabelle (IST), Formular (offen), Validierung beim Import (IST), Speichern/Export UI (offen).
2) Metrics: realized PnL, Win-Rate, Profit-Factor, realized MaxDD (IST); CAGR, Holding-Dauer (offen).
3) Patterns: Histogramme Holding-Dauer, Scatter Entry vs Return (offen).
4) Simulation: Basissimulation (Seed) (IST); Parameter (tp%, sl%, rebalance_days, cost bps) (offen); Persistenz data/results/ (offen).
5) Live Quotes (optional): komplett offen.

Non-blocking: Geplant – jeder Sim-Run soll unter data/results/{timestamp}_{hash}/ schreiben (noch offen).
