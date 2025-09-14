# RAG Context Policy (Aktualisiert)

Sources:
- Nur lokale Dateien (`data/notes/*`, `data/cache/*`, DecisionCard Inhalte optional). Keine externen Netzquellen / API Calls.

Constraints / Anti-Bias:
- (Geplant) Filter `(ticker, as_of)` → Dokumente mit Zeitstempel > as_of ausgeschlossen (Look-Ahead Vermeidung).
- Deterministische Segmentierung (Hash aus Pfad + Offset) für Repro.
- Max Chunks: 8 (Soft Cap); Gesamt Tokens Zielkorridor 800–1200 (Heuristik, später konfigurierbar).

Ranking Modi:
1. Basic (Default): Term-Frequenz (lexical) + simple snippet extraction.
2. Advanced (`VEK_RETRIEVAL_ADV=1` oder Parameter): Weighted Boosts (Titel > Überschriften > Body) + token normalization.
3. Embedding (`VEK_RETRIEVAL_EMB=1` oder Parameter): Deterministische Pseudo-Embeddings (SHA256 Hash Bigrams) → Cosine Similarity Ranking. Kein echter semantischer Raum (Experiment / Platzhalter).

Hybrid (Geplant): Score Fusion (lexical_norm * α + embedding_sim * (1-α)) + Temporal Decay Boost.

Feature Flags:
| Flag | Wirkung |
|------|---------|
| `VEK_RETRIEVAL_ADV` | Aktiviert Advanced Scoring Pipeline |
| `VEK_RETRIEVAL_EMB` | Aktiviert Embedding Ranking (überschreibt advanced falls beide gesetzt, fallback advanced wenn embedding deaktiviert) |

Determinismus:
- Pseudo-Embeddings erzeugen deterministische Vektoren (kein RNG), testbar via Snapshot / Ranking Order.

Security / Isolation:
- Keine Remote Calls; ausschließlich lokale Lesezugriffe.
- Kein Speichern sensibler Inhalte in temporären externen Stores.

Output Schema (Aktuell):
`[{"doc_id": str, "score": float, "snippet": str}]` – snippet extrahiert ersten passenden Kontextblock (TODO: Multi-Snippet Merge für spätere Iterationen).

Planned Enhancements:
- Ticker/As-Of Filtering Implementierung + Tests.
- Hybrid Score Fusion + Recency Boost.
- Embedding Vector Cache (Hash Key) für Performance (wenn echte Embeddings eingeführt).
- Multi-Snippet Aggregation & Sentence Boundary Respect.

Testing Policy:
- Ranking determinism tests (same query → identical order).
- Mode separation tests (basic vs advanced vs embedding produce expected ordering differences).
- Negative case: empty corpus → leere Liste.

Backlog: Siehe Roadmap Tabelle (I1–I5 für indirekte Anforderungen an Retrieval Kontext). Retrieval Filter weiterhin offen.
