# DecisionCard Spec (JSON)

{
  "ticker": "NVDA",
  "as_of": "YYYY-MM-DD",
  "thesis": "Kurzbegründung",
  "evidence": ["data/notes/nvda_thesis.md", "data/cache/news/NVDA_2025-06-01.txt"],
  "metrics": {"cagr": 0.31, "maxdd": 0.18, "win_rate": 0.62},
  "action": {"type": "hold|add|trim|exit", "target_w": 0.07, "ttl_days": 120},
  "risks": ["Rate shock", "Supply constraints"],
  "confidence": 0.0-1.0
}
  Status: TEIL-IMPLEMENTIERT: Dataclass (`core/decision_card.py`) enthält aktuell NUR Basisfelder (card_id, created_at, author, title, context_refs, assumptions, options, decision, rationale, metrics_snapshot). Fehlend: action{type,target_w,ttl_days}, risks, confidence. `maxdd` Ziel: Equity Curve (heute nur realized Variante). → Backlog P0 DecisionCard Feld-Divergenz.

Backlog: DecisionCard Feld-Divergenz (#2) — siehe tmp_backlogCollection.md
