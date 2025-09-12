# Test Strategy

Smoke:
- trades.csv Roundtrip (implementiert)
- analytics: realized PnL, realized MaxDD, Win-Rate, Holding-Dauer Durchschnitt (implementiert) — unrealized / CAGR / Patterns offen
- equity curve realized (implementiert)
- sim: deterministischer Run + Persistenz Ordnerstruktur (implementiert)

Regression:
- Bei Änderungen an sim/analytics geplanter Snapshot-Vergleich (noch offen).

Open Items (Quelle Roadmap, keine Duplizierung): Unrealized Equity Curve, Pattern Analytics, Snapshot Regression, DecisionCard UI Tests, Retrieval Filter Tests, CAGR.

Backlog: CAGR (#6), Unrealized Equity Curve (#7), Pattern Analytics (#8), Snapshot Regression Tests (#9) — siehe tmp_backlogCollection.md
