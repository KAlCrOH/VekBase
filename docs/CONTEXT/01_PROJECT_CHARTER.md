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
- Trades laden/anzeigen & eingeben (Form + CSV Validierung) — Implementiert.
- Basis-Kennzahlen (realized PnL, Win-Rate, Profit-Factor, realized Max Drawdown, realized Equity Curve) — Implementiert.
- Einfache Walk-Forward-Simulation (Seed + Hash) — Implementiert.
- Reprozierbarkeit (Seed + Hash) — Implementiert.
- Developer Productivity: Frontend-first Konsole mit Pytest Runner — Implementiert.
- Offene Punkte: Simulation Persistenz, Pattern-Mining, Holding-Dauer, DecisionCards, RAG, Live Quotes.
