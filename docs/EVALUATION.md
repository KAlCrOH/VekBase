# EVALUATION – Qualität & Regressionsschutz

Ziel: Sicherstellen, dass Retrieval & Generierung nachvollziehbar verbessern und keine stille Degradation eintritt.

## Kernmetriken
| Metrik | Formel (Skizze) | Bedeutung |
|--------|-----------------|-----------|
| Recall@k | rel_in_top_k / total_relevant | Abdeckung relevanter Chunks |
| MRR | mean(1 / rank_first_rel) | Frühzeitige Treffergüte |
| nDCG@k | DCG@k / IDCG@k | Rankingqualität |
| Coverage Score (geplant) | matched_context_tokens / answer_tokens | Antwort stützt sich auf Kontext |
| Rerank Lift | (MRR_rerank - MRR_base)/MRR_base | Nutzen des Rerankers |

## Datensätze
| Set | Quelle | Nutzung |
|-----|--------|---------|
| train (optional) | synthetisch QA aus Chunks | Rerank Tuning |
| eval | Handkuratierte Query→Chunk Relevanz | Metriken |
| drift-baseline | Snapshot Embeddings | Drift Detection |

## Bundle Nutzung
Bundles liefern: query, contexts, prompt, (später completion). Zur Coverage & Prompt-Stabilität:
1. Lade Bundles
2. Tokenisiere completion + contexts
3. Zähle Kontext-Token, die in completion erscheinen
4. Coverage Score berechnen

## Experimentdesign
| Experiment | Variation |
|------------|----------|
| K Sweep | k ∈ {3,5,8,10} |
| Chunk Size | 250 vs 350 vs 500 Tokens |
| Rerank On/Off | Qualitätslift |
| Hybrid On/Off | Robustheit Keywords |

## Reporting
- JSON Summary: metrics.json (pro Commit in CI)
- Trend Plot (Notebook)

## Regression Gate (Geplant)
Fail CI wenn:
- MRR_drop > 5% gegenüber main
- Recall@k_drop > 5%
- Coverage Score < 0.6

## Nächste Schritte
1. Eval Ground Truth Schema definieren
2. Skript: compute_metrics.py
3. CI Hook integrieren
