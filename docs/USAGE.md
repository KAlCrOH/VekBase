# Nutzung & Operation

## .env Variablen (Kern)
Siehe `CONFIG.md` für vollständige Liste.

## CLI Kommandos
| Command | Zweck | Status |
|---------|------|--------|
| ingest | Rohdaten → Normalize → Split → SQLite | Basis |
| index | Liest Chunks → Embeddings → FAISS Build | LIMIT aktuell |
| query | Retrieval (optional LLM) | Basis |
| (geplant) verify | Audit Hash Verifikation | Pending |

## Flags / Optionen (Geplant)
| Option | Kontext | Wirkung |
|--------|---------|--------|
| --rerank | query CLI / API | Aktiviert Reranker |
| --stream | query API | SSE Streaming Token-Ausgabe |
| --retrieval-only | query | Unterdrückt LLM Call |
| --filters source_path= | query | Einschränkung Quelle |

## API Übersicht
- GET /health → `{ status: "ok" }`
- POST /query `{ query, top_k?, rerank?, retrieval_only? }`
	- Antwort enthält optional `bundle_id` wenn bundling aktiv

## Prompt & Bundles
- Templates: `src/app/rag/prompt/`
- Bundles: `data/bundles/*.parquet`
- Enthalten: query, chunk_ids, contexts, prompt_filled (künftig hashes)

## Audit Hinweise
- Für jede Query entsteht ein Bundle (wenn LLM oder bundling aktiv)
- Rekonstruktion: Siehe `AUDIT.md`

## Admin API (Geschützt)
`X-Admin-Key` Header erforderlich.

| Endpoint | Zweck |
|----------|------|
| GET /admin/bundles | Letzte Bundles listen |
| GET /admin/bundles/verify?path=... | Basis-Validierung eines Bundles |
| POST /admin/chat { message, retrieve? } | Chat mit optionalem Retrieval-Kontext |
| POST /admin/reindex | (Stub) Index Neuaufbau anstoßen |

## Entwicklungs-Workflow (Empfohlen)
1. Neue Rohdaten in `data/raw/`
2. `ingest` ausführen
3. `index` (neu bauen bei Model / Pipeline Änderung)
4. `query` testen
5. Metriken & Logs prüfen (`OBSERVABILITY.md`)

## Fehlerbehandlung
| Problem | Maßnahme |
|---------|----------|
| Index fehlt | `index` erneut ausführen |
| Model nicht gefunden | EMBEDDING_MODEL prüfen |
| LLM Timeout | retrieval-only Pfad verwenden |
| Dim mismatch | VECTOR_DIM + Index rebuild |

## Nächste Schritte
1. Streaming Implementierung
2. Verify CLI
3. Rerank Flag produktiv
