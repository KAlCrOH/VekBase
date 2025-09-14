## Backlog Collection (Consolidated)

Legende Typ: bug | debt | doc | test | design

### P0
[DONE] UI SimResult Rückgabemismatch — Modul: ui.console
[DONE] DecisionCard Feld-Divergenz — Modul: core.decision_card

### P1
[P1][design] Retrieval Filter & Snippet Qualität — Modul: core.retrieval — Typ: DONE
 * Implementiert: ticker & as_of Filter (Datumsvalidierung) + Limit Parameter im UI.
 * Next: Relevanz Ranking (Heuristik: Gewichtung Trefferhäufigkeit + Feldgewicht), Option "excerpt" Länge begrenzen.
[P1][design] Erweiterte Sim Parameter (TP/SL/Kosten) — Modul: sim.simple_walk — Typ: fehlend
 * Nur Basis-Parameter vorhanden.
 * Next: Parameter definieren (take_profit_pct, stop_loss_pct, fee_perc), Persistenz Hash erweitern, deterministischer Regressionstest.
[P1][doc] Architektur-Doku Folgepflege — Modul: documentation — Typ: laufend
 * Pflege nach jedem Increment; letzte Aktualisierung nach Benchmark Overlay & Snapshot Erweiterung noch offen.
 * Next: Abschnitt "Analytics Layer" ergänzen (Benchmark / Volatilität), Snapshot Ziele-Liste aktualisieren.
[P1][design] Unrealized Equity Curve Erweiterung — Modul: analytics.metrics/ui.console — Typ: DONE
 * Implementiert: aggregate unrealized timeline, per‑Ticker timeline, Total (realized+unrealized) Punkt, Altair Multi-Series (realized/unrealized/total/benchmark/rolling_vol).
 * Snapshot Targets erweitert (equity_curve_unrealized, equity_curve_per_ticker). Tests grün.
 * Next: Farb- und Theme-Konfiguration zentralisieren (Dark/Light Paletten), optional Prozent-Normalisierung vs Startkapital.

### P2
[P2][design] Erweiterte Pattern Analytics — Modul: analytics.patterns — Typ: DONE
 * Neu: overflow_count, p95, tail_left/right counts, return_distribution erweitert (p90/p95, tails).
 * Next: Optionale Kennzahlen (skew, kurtosis) hinter Flag; Per-Ticker Pattern Aggregation.
[P2][test] Snapshot Regression Coverage Ausbau — Modul: tests/snapshots — Typ: PARTIAL
 * Targets erweitert: metrics, equity_curve, equity_curve_unrealized, equity_curve_per_ticker.
 * Next: Simulation Equity Snapshot + Benchmark Overlay Baseline (normierter Start bei 0), Automatisierte Delta-Schwellwerte.
[P2][design] Queue Aggregate Metrics — Modul: core.testqueue — Typ: DONE
 * Median & p95 Duration ergänzt; Reset Helper für Testisolation; UI Anzeige.
 * Next: Rolling Window Failure Rate (letzte N), SLA Warnschwelle (Duration > p95_baseline).
[P2][design] Queue Retention Policy — Modul: core.testqueue — Typ: DONE
 * Implementiert: _apply_retention mit VEK_TESTQUEUE_MAX_RUNS / VEK_TESTQUEUE_MAX_BYTES; Silent-Fails vermieden.
 * Next: UI Konfig Panel + Metrik für aktuelle Output Dir Size.
[P2][test] DecisionCard/Retrieval UI Tests — Modul: ui.console — Typ: offen
 * Noch keine gezielten UI Smoke Tests.
 * Next: Minimaler Headless Test (validate repository side-effects) + Retrieval Filter Assertions.
[P2][debt] Testqueue Persistence Error Handling Verfeinerung — Modul: core.testqueue — Typ: DONE
 * Counters + get_persistence_stats integriert; Workbench Panel zeigt Stats.
 * Next: Error Rate Badge + Alert bei >0 Errors.
[P2][debt] Redundante Status-Mapping Kommentare — Modul: core.testqueue — Typ: DEFER
 * Belassen bis zusätzliche Stati (skipped/xfailed) implementiert.
 * Next: Design Abschnitt "Extended Status Lifecycle" ergänzen.

### P3
[P3][design] Live Quotes Cache — Modul: (neues Submodul) — Typ: fehlend
 * Bisher kein Feed; optional.
 * Next: Interface Entwurf + Mock Implementation.
[P3][design] Optionale Embeddings/RAG Ranking — Modul: retrieval — Typ: fehlend
 * Policy erlaubt optional; aktuell rein lexical.
 * Next: Evaluieren minimalen Embedding Layer (abschaltbar) – separate Entscheidung.

### Notes
- Datei aktualisiert nach Implementierung: Benchmark Overlay, Rolling Volatility, Snapshot Target Erweiterung, Queue p95/Median, Retention Policy, Pattern Tail Stats.
- Roadmap referenziert high-level; diese Datei = Single Source für Feingranularen Status.
- Default Demo Dataset (VEK_DEFAULT_DATA=1) belassen für schnelle Visualisierung.
- Feature Flags aktuell: VEK_ANALYTICS_EXT, VEK_PATTERNS, VEK_DEVTOOLS, VEK_DECISIONCARDS, Retention via VEK_TESTQUEUE_MAX_RUNS / VEK_TESTQUEUE_MAX_BYTES.
- Nächster Fokus (vorgeschlagen): Sim Parameter Erweiterung (P1), Snapshot Coverage für Benchmark, UI Test Smoke Pass.
