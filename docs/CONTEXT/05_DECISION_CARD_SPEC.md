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
  Status: AKTUALISIERT (prompt3_roadmap_implement): Dataclass (`core/decision_card.py`) enthält jetzt zusätzliche Felder `action{type,target_w,ttl_days}`, `risks`, `confidence` mit Validierung (type ∈ hold|add|trim|exit; confidence ∈ [0,1]). Backlog-Item Feld-Divergenz erledigt.

Backlog (Update): Entfernt DecisionCard Feld-Divergenz (#2) – verbleibend: Equity Curve unrealized / Patterns.
