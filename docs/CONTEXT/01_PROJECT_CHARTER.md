# Project Charter — Personal Investor Workbench (KISS)

Scope: Ein rein persönliches, lokales Tool zur Analyse meiner Trade-Historie, Mustererkennung, leichter Simulationen und optionaler LLM/RAG-Unterstützung. Keine Enterprise-Funktionen.

Principles:
- KISS, lokal-first, verständlicher Code.
- Eine zentrale Admin-Oberfläche (Streamlit).
- Manuelle Trade-Erfassung (CSV + Validierung).
- Kostenloser Betrieb standardmäßig (Live-Kurse optional mit Cache).
- LLM/RAG nur als optionale Add-ons (kein Zwang).

Non-Goals:
- Kein Auto-Sync mit Brokern.
- Keine Mehrbenutzer-Features.
- Keine komplexe MLOps/Cloud.

Success Criteria (MVP Status):
- Implementiert: Trade Erfassung/Validierung, Basis-Kennzahlen (realized PnL, Win-Rate, Profit-Factor, realized Max Drawdown, realized Equity Curve, CAGR), einfache Walk-Forward-Simulation (Seed+Hash), Reproduzierbarkeit (Seed+Hash), Frontend-first Konsole (DevTools inkl. Queue), DecisionCard Felder.
- Offene Punkte (Kurzreferenz, Details siehe Backlog): Unrealized Equity Curve Erweiterung, Erweiterte Pattern Analytics, Erweiterte Sim-Parameter, Retrieval Filter (ticker/as_of) & Snippet Qualität, Snapshot Regression Coverage Ausbau, Live Quotes Cache (optional), Queue Aggregatsmetriken & Retention.
- Charter listet keine Detail-Backlogs → zentrale Quelle: `CONTEXT/09_ROADMAP_MVP.md` + `docs/DOCUMENTATION/tmp_backlogCollection.md`.

Backlog Referenzen (Kurz): Siehe aktuelle IDs im Backlog (`tmp_backlogCollection.md`).
Backlog: Testqueue Persistenz & Status-Klarheit (#P2-debt-testqueue) — siehe tmp_backlogCollection.md
