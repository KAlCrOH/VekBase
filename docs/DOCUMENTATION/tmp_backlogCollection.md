## Backlog Collection (Consolidated)

Legende Typ: bug | debt | doc | test | design

### P0
[#1][design] UI SimResult Rückgabemismatch — Modul: ui.console — Owner: <tbd> — STATUS: DONE
 - Kontext: console erwartete res['folder']; `SimResult` hatte kein Feld. Implementiert: folder Attribut + UI Zugriff.
 - Next: (none)
[#2][design] DecisionCard Feld-Divergenz — Modul: core.decision_card — Owner: <tbd>
 - Kontext: Spec listet action{type,target_w,ttl_days}, risks, confidence – Dataclass enthält sie nicht.
 - Vorschlag Next Step: Optionale Felder hinzufügen (Default None), Tests erweitern (Backward-Kompatibilität sicherstellen).

### P1
[#3][design] Retrieval Filter (ticker, as_of) — Modul: core.retrieval — Owner: <tbd>
 - Kontext: RAG Policy Ziel sieht Filter vor; Stub nur Keyword Count.
 - Vorschlag Next Step: retrieve(query, ticker=None, as_of=None, limit=3) + einfacher Dateiname/Zeit Filter.
[#4][doc] Architektur-Doku Folgepflege — Modul: documentation — Owner: <tbd>
 - Kontext: Aktualisierte Struktur; zukünftige Feature-Erweiterungen müssen zeitnah eingepflegt werden.
 - Vorschlag Next Step: Review Checklist nach jedem P0/P1 Merge.
[#5][design] Erweiterte Sim Parameter (TP/SL/Kosten) — Modul: sim.simple_walk — Owner: <tbd>
 - Kontext: UI Spec & Roadmap listen Parameter als offen.
 - Vorschlag Next Step: Parameter + Hash-Eingang definieren; Test für Reproduzierbarkeit.

### P2
[#6][design] CAGR Berechnung — Modul: analytics.metrics — Owner: <tbd> — STATUS: DONE
 - Kontext: Realisierte Equity Curve Basis; CAGR Funktion implementiert + Tests (positiv & Edge).
 - Next: (none)
[#7][design] Unrealized Equity Curve — Modul: analytics.metrics — Owner: <tbd>
 - Kontext: Nur realized Kurve implementiert; unrealized Kennzahlen geplant.
 - Vorschlag Next Step: Offene Positionen mit mark_prices fortschreiben (Baseline = realized curve).
[#8][design] Pattern Analytics Grundfunktionen — Modul: analytics (patterns.py) — Owner: <tbd>
 - Kontext: UI Patterns Tab leer; benötigt Kernberechnungen (Histogram, Scatter Daten).
 - Vorschlag Next Step: Funktionen generate_holding_hist(trades) & entry_return_scatter(trades) + Tests.
[#9][test] Snapshot Regression Tests — Modul: tests — Owner: <tbd> — STATUS: PARTIAL (DevTools Runner Basis vorhanden)
 - Kontext: Test Runner UI hinzugefügt (Filter/Status/Logs). Snapshot Mechanismus noch offen.
 - Next: Implement Golden File Hash/Fingerprint Tests (sim + metrics) in separatem Increment.
[#10][design] DecisionCard / Retrieval UI Panels — Modul: ui.console — Owner: <tbd>
 - Kontext: Kein Tab für DecisionCards/Retrieval Anzeige.
 - Vorschlag Next Step: Neues Tab mit minimaler List-/Detailanzeige (keine LLM Funktionalität).

### Notes
- Roadmap bleibt Quelle für Prioritäten. Diese Datei enthält normalisierte, ID-bezogene Items.
