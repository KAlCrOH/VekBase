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
- Implementiert: Trade Erfassung/Validierung, Basis-Kennzahlen (realized PnL, Win-Rate, Profit-Factor, realized Max Drawdown, realized Equity Curve), einfache Walk-Forward-Simulation (Seed+Hash), Reproduzierbarkeit (Seed+Hash), Frontend-first Konsole (Pytest Runner).
- Offene Punkte (Quelle: ROADMAP): CAGR, unrealized PnL/Equity Curve, Pattern Analytics, DecisionCards (erweitert), Retrieval Filter & RAG, erweiterte Sim-Parameter, Live Quotes.
- Charter listet keine Detail-Backlogs → zentrale Quelle: `CONTEXT/09_ROADMAP_MVP.md`.

Backlog Referenzen (Kurz): Kern offene Punkte IDs #1 #2 #3 #5 #6 #7 #8 #9 #10 — siehe tmp_backlogCollection.md
