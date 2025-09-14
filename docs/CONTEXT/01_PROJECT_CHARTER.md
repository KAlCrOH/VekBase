# Project Charter — Personal Investor Research & Strategy Workbench

Scope (aktualisiert): Lokale Forschungs- und Analyse-Umgebung zur Evaluierung, Vergleichbarkeit und Governance von Aktien-Strategien. Neben Basis-Analytics jetzt Fokus auf: Robustheitsanalyse (Parameter-Sweeps), Regime-Konditionierung, Faktor-Attribution, Portfolio-Konstruktion, Risiko-/Fehlermuster-Erkennung sowie dokumentierte Entscheidungs-/Review-Prozesse (Decision Cards) – alles lokal-first, optional erweitert durch Retrieval/LLM.

Principles (unverändert + erweitert):
- KISS, lokal-first, verständlicher Code.
- Einheitliche Admin-/Analytics-Konsole (Streamlit) mit dunklem/hellem Theme.
- Manuelle oder skriptgestützte Trade-Erfassung (CSV + Validierung).
- Kostenneutraler Standardbetrieb (Live Quotes optional / später).
- Moduläre Feature Flags für risk/attribution/portfolio/embeddings.
- Determinismus & Reproduzierbarkeit (Seeds, Hashes, Snapshots).
- Transparente Governance: DecisionCard Workflow (draft→proposed→approved|rejected mit Reviewer & Expiry).
- Robuste Tests als Entwicklungs-Gateway (keine ungetesteten Kernpfade).

Non-Goals:
- Kein Auto-Sync mit Brokern.
- Keine Mehrbenutzer-Features.
- Keine komplexe MLOps/Cloud.

Delivered (aktueller Stand):
- Erweiterte Simulation (TP/SL/Fee), erweitertes Risiko (VaR, ES, Rolling VaR), erweiterte Retrieval Modi (Advanced + Embedding), Dark Mode UI.
- DecisionCard Workflow mit Validierung & Expiry.
- Snapshot- & Test-Suite Ausbau (96 Tests, Risk Flags, Workflow, Embeddings).

Success Criteria (erweitert):
1. Robuste Metriken: Realized & Risk (VaR/ES) + Erweiterungen ohne Breaking Changes.
2. Forschung: Vergleich mehrerer Strategien (Batch Runner) → Sensitivität & Robustheitsscores.
3. Kontextualisierung: Regime-Kennzeichnung & Faktor-Attribution trennen Edge vs Beta.
4. Portfolio: Diversifikation & Kapitalallokation (Optimierungs-Policies) geplant.
5. Governance: Entscheidungs-/Review-Prozess nachvollziehbar (Status, Reviewer, Ablaufdatum).
6. Lernschleife: Verlustmuster-Clustering zur Hypothesen-Generierung (Failure Miner) geplant.

Open (Top-Prioritäten – Details siehe Roadmap):
- Strategy Batch Runner, Regime Detection, Factor Attribution, Portfolio Optimizer, Failure Pattern Miner.
- Flag-Zentralisierung, Snapshot-Fuzzy-Toleranzen, Audit Trail.

Referenzen:
- Roadmap: `CONTEXT/09_ROADMAP_MVP.md`
- Teststrategie: `CONTEXT/07_TEST_STRATEGY.md`
- Flags & Inkremente: Roadmap Feature Flag Tabelle.
- Historische Backlog-Einträge: `docs/DOCUMENTATION/tmp_backlogCollection.md` (Legacy / Traceability).
