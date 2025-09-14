# Roadmap (MVP → +RAG/LLM)

MVP (P0-P3) Status: Basis implementiert (Charter, Schema, UI Grundfunktionen, realized Analytics inkl. CAGR, simple Sim, DevTools Queue, Tests, DecisionCard Felder).
Aktuelle Prioritäten (vereinheitlicht, detaillierte Begründungen im Backlog):
P0 (none – aktuelle Basis stabil)
P1
 - Retrieval Filter (ticker, as_of) & Snippet Qualität
 - Erweiterte Sim-Parameter (TP/SL/Kosten)
 - Architektur-Doku Folgepflege (laufend)
 - Unrealized Equity Curve Erweiterung
P2
 - Erweiterte Pattern Analytics (beyond basic Histogram/Scatter)
 - Snapshot Regression Coverage Ausbau
 - DecisionCard/Retrieval UI Tests & Erweiterungen
 - Queue Aggregate Metrics & Retention Policy
P3
 - Live Quotes Cache (optional)
 - Optionale Embeddings/Rerank (RAG Erweiterung)

Später: Live Quotes Cache, Embeddings, LLM Integration.

Backlog Referenzen: Siehe konsolidierte Liste in `docs/DOCUMENTATION/tmp_backlogCollection.md` (IDs rotierend gepflegt, erledigte entfernt).
Backlog: Silent Persistenz Error Handling + Status Erweiterungs-Entscheid (#P2-debt-testqueue) — siehe tmp_backlogCollection.md

