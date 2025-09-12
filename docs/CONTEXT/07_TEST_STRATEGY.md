# Test Strategy

Smoke:
- trades.csv Roundtrip (implementiert).
- analytics: realized PnL Sum, realized MaxDD, Win-Rate (implementiert).
- sim: deterministischer Run (Seed + Hash) (implementiert).

Regression:
- Bei Änderungen an sim/analytics geplanter Snapshot-Vergleich (noch offen).

Open Items:
- Equity Curve (unrealized) Tests.
- Holding-Dauer & Pattern Tests.
