# Architektur – VekBase (Auditable RAG & Agent Readiness)

Ziel: Ein lokales, erweiterbares Retrieval-Augmented-Generation (RAG) Fundament mit klaren Schichten, Auditierbarkeit (Kontext-Nachvollziehbarkeit), Agenten-Orchestrierung und späterer Option für lokale & Remote LLMs.

## 1. End-to-End Fluss
1. Ingest: Rohquellen → Normalisierung → Chunks → Metadaten Persistenz (SQLite + optional Parquet)
2. Embedding: Batch Embedding der Chunks (SentenceTransformers) → Vektor Matrix
3. Indexierung: FAISS Index (Flat → optional IVF/HNSW) persistiert auf Disk
4. Query: Nutzerfrage → Query Embedding → Top-K Vektor-Suche → (optional Filter/Rerank)
5. Prompt-Build: Kontext-Assemblierung + Template → Chat Nachrichtenliste
6. LLM Call: OpenAI-kompatibel (Remote / vLLM / Ollama)
7. Bundling & Audit: Parquet Bundle (Query, Kontexte, Prompt, Modell, Scores, Timestamps)
8. Evaluation / Monitoring: Offline Metriken & Observability (Logs + Traces)

## 2. Schichten & Verantwortlichkeiten
| Schicht | Verzeichnis | Verantwortung | Erweiterungspunkte |
|---------|-------------|---------------|--------------------|
| Core | `core/` | Konfig, Logging, Tracing, IDs | Security, Multi-Env | 
| Ingest | `rag/ingest/` | Loader, Normalisierung, Chunking | Neue Dateitypen, Validierung |
| Embed | `rag/embed/` | Embedding Modelle | GPU Optimierung, Model Switch |
| Store | `rag/store/` | Metadaten + Index | Alternative Indizes (HNSW, DiskANN) |
| Retrieve | `rag/retrieve/` | Top-K Retrieval | Filter, Hybrid, Rerank |
| Rerank | `rag/rerank/` | Qualitätssteigerung | Cross-Encoder, LLM Judge |
| Prompt | `rag/prompt/` | Templates, Bundles | Token-Budget Mgmt, Mehrsprachigkeit |
| LLM | `rag/llm/` | OpenAI-kompatible Calls | Provider Orchestrierung |
| Orchestrator | `api/orchestrator.py` | Ablauf-Koordination | Agenten, Tool Calls |
| API | `api/routes_*.py` | HTTP Surface | AuthZ, Rate Limits |

## 3. Auditierbarkeit & Nachvollziehbarkeit
Audit-Ziel: Jede Antwort muss auf die verwendeten Chunks + Prompt + Modellversion zurückführbar sein.
Mechanismen:
- Stable Chunk IDs (`ids.py`) deterministisch aus (source, text)
- Bundles (Parquet): query, contexts[], scores, prompt (system+user), provider, model, timestamps
- Log Felder (structlog): request_id, stage, latency_ms, top_k, chunk_ids, model, vector_dim
- Optional: Hash des finalen Prompts → Wiederholbarkeit / Integrity Check

## 4. Sicherheits- & Vertrauensmodell (High-Level)
Kurzfristig: Single-User Entwicklungsumgebung.
Vorbereitung für später:
- Input Validation (Max Query Länge, UTF-8 Normalisierung)
- Chunk Content Hashing (Erkennung von Manipulationen)
- Signierte Bundle Manifeste (optional, zukünftige Governance)

## 5. Datenlebenszyklus
| Phase | Artefakt | Speicher | Retention Idee |
|-------|----------|----------|----------------|
| Ingest | Rohdatei | `data/raw` | Manuell/kurz |
| Processing | Normalisierte Chunks | Parquet (geplant) | Versionsbasiert |
| Index | Vektorindex | FAISS Datei | Neuaufbau bei Modellwechsel |
| Query | Prompt + Kontext | Bundle Parquet | N Tage / Anonymisierung |
| Evaluation | Metriken | Reports / Notebook | Historisch verdichtet |

## 6. Erweiterungspunkte
- Embeddings: beliebige HF Modelle / NVIDIA, austauschbar via ENV
- Index Varianten: IVF/HNSW Parameter in Config
- Rerank: Cross-Encoder Score fusion (weighted) / LLM Re-Rank Agent
- Hybrid Retrieval: BM25 (Elastic/Lucene) + Vektor-Kombi mit Normalisierung
- Tool Agents: Wissensgraph Query, Structured DB Lookup, Summarizer

## 7. Agenten-Vision (Vorbereitung)
Geplante Rollen:
- RetrievalAgent: Strategien (dense, hybrid) & Budget
- ValidationAgent: Prüft Kontext gegen Policy (PII Removal, Confidence)
- ReasoningAgent: Baut rationale Zwischenschritte (Chain-of-Thought optional intern)
- ExecutionAgent: Koordiniert Tools (DB, APIs)
- AuditAgent: Überwacht Bundles & pflegt Audit-Index

Aktuelle Umsetzung: Orchestrator stub als Einstieg – Schnittstellen klein halten.

## 8. Datenmodell (Kurzreferenz)
Siehe detailliert: `DATA_MODEL.md`.
Wesentliche Objekte: Document, Chunk, RetrievalResult, Bundle.

## 9. Observability
Traces: Anfrage → Embedding → VectorSearch → (Rerank) → Prompt → LLM → BundleWrite
Logs: JSON, strukturierte Felder (siehe `OBSERVABILITY.md`).

## 10. Konfiguration
ENV zentrisch (`config.py`), keine versteckte globale Zustände.
Alle Pfade / Modellnamen / Parameter versionierbar über `.env`.

## 11. Roadmap Snapshot
- Batch Embedding Pipeline (Parquet) – Priorität Hoch
- Rerank Integration
- Streaming Antworten & Token Budget Manager
- Sicherheits-/Governance Layer (Validierung + Redaction)
- Agent Framework (Execution Graph)

## 12. Admin & Audit Interface
Komponenten:
- Admin Router: `/admin/*` (geschützt via API Key)
- Funktionen: Bundle Listing, Bundle Verify, Admin Chat, Reindex Stub
- Audit Verify: Parquet Einzelbundle lesen → (zukünftig) Hash Vergleich prompt/completion

Sequenz (Verify): Client → GET /admin/bundles → wählt Pfad → GET /admin/bundles/verify?path=… → Ergebnis (Match/Fehlend)

## 13. Risiken & Mitigation
| Risiko | Wirkung | Mitigation |
|--------|--------|------------|
| Index Inkonsistenz (Metadaten vs. FAISS) | Falsche Kontexte | Rebuild Hash + Konsistenzcheck |
| Kontext-Overflow Prompt | LLM Fehlverhalten | Token Budget Manager (Trimming) |
| Modellwechsel ohne Reindex | Qualitätsverlust | Index Version Tag + Rebuild Pipeline |
| Fehlende PII Redaction | Compliance Risiko | ValidationAgent + RegEx/NER Filter |

## 14. Glossar
- Chunk: Kleinste Retrieval-Einheit
- Bundle: Persistierter Kontext- und Prompt-Datensatz
- Rerank: Zweite Ranking-Pipeline zur Qualitätssteigerung
- Hybrid Retrieval: Kombination Dense + Lexikalisch

---
Nächste Schritte: Parquet Ingest + Batch Indexierung implementieren, dann Rerank & Token Budget, Hash-Felder im Bundle + Admin Verify Ausbau.
