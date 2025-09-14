# Test Strategy

Smoke:
- trades.csv Roundtrip (implementiert)
- analytics: realized PnL, realized MaxDD, Win-Rate, Holding-Dauer Durchschnitt, CAGR (implementiert) — unrealized Erweiterung / erweiterte Patterns offen
- equity curve realized (implementiert)
- sim: deterministischer Run + Persistenz Ordnerstruktur (implementiert)

Regression:
- Bei Änderungen an sim/analytics geplanter Snapshot-Vergleich (noch offen).

Open Items (Kurzreferenz – Details ausschließlich im Backlog): Unrealized Equity Curve, Erweiterte Pattern Analytics, Snapshot Regression Coverage Ausbau, DecisionCard/Retrieval UI Tests, Retrieval Filter Tests.

Backlog: Siehe `docs/DOCUMENTATION/tmp_backlogCollection.md` (IDs aktualisiert; erledigte Items wie CAGR entfernt).
