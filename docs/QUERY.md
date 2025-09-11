# QUERY – Retrieval & Orchestrierung

Endpunkt: `POST /query { query, top_k? }`

## Ablauf
1. Query Embedding (Embedder)
2. Vektor-Suche in FAISS (FlatIP aktuell)
3. Chunk-Metadaten Join (SQLite)
4. (Optional) Rerank (geplant)
5. Prompt Build (Template + Kontexte)
6. (Optional) LLM Call (konfigurierbar)
7. Bundle Write (Parquet)

## Request/Response (Beispiel)
Request:
```
{ "query": "Wie funktioniert die Pipeline?", "top_k": 5 }
```
Response (gekürzt):
```
{
	"query": "...",
	"results": [ {"chunk_id": "...", "text": "...", "score": 0.83 } ],
	"bundle_id": "..." (wenn LLM + bundling aktiv)
}
```

## Retrieval Parameter
| Parameter | Quelle |
|-----------|--------|
| top_k | Body / Default TOP_K |
| index_type (future) | ENV / Query Param |
| rerank | Query Param Flag |

## Audit Hooks
- Log Events: `retrieve.request`, `retrieve.result`, `prompt.built`, `bundle.written`
- bundle.parquet enthält query, selected chunk_ids, prompt

## Erweiterungen (Geplant)
| Feature | Nutzen |
|---------|-------|
| Rerank (Cross-Encoder) | Qualitätslift Relevanz |
| Hybrid (BM25 + Dense) | Robustheit bei Keywords |
| Filter (Pfad / Tags) | Kontrollierte Subsets |
| Streaming Antwort | Schnellere Partial-Outputs |
| Cache Layer | Niedrigere Latenz für Hot Queries |
| Score Normalisierung | Vergleichbarkeit über Index-Typen |

## Fehlerfälle
| Situation | Verhalten |
|----------|-----------|
| Keine Treffer | leeres results Array |
| Dim Mismatch | 500 + Log (Index rebuild nötig) |
| LLM Timeout | Rückgabe retrieval-only + Warnfeld |

## Prioritäten Nächster Sprint
1. Rerank Flag + Stub Integration
2. Hybrid Retrieval Design (BM25 SQLite FTS5)
3. Streaming (Server-Sent Events)
4. Filter by source_path (Query Param)
