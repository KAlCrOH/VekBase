# Test Strategy

Smoke:
- trades.csv Roundtrip (implementiert)
- analytics: realized/unrealized PnL, realized MaxDD, Win-Rate, Holding-Dauer Durchschnitt (implementiert)
- equity curve realized (implementiert)
- sim: deterministischer Run + Persistenz Ordnerstruktur (implementiert)

Regression:
- Bei Änderungen an sim/analytics geplanter Snapshot-Vergleich (noch offen).

Open Items:
- Equity Curve (unrealized) (noch nicht implementiert)
- Pattern Analytics (Histogramme, Scatter)
- Simulation Snapshot Regression (geplant)
- DecisionCard UI & Retrieval Panel Tests
