# DecisionCard Spec (JSON + Workflow)

Minimaler Kern (Inhalt):
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

Erweiterung (Workflow Felder – implementiert):
{
  "status": "draft|proposed|approved|rejected",
  "reviewers": ["analystA", "leadB"],
  "approved_at": "2025-09-14T12:00:00Z | null",
  "expires_at": "2025-12-14T12:00:00Z | null"  // gesetzt bei approval + action.ttl_days
}

Validierungsregeln (implementiert in `ActionSpec.validate` + Fabrikfunktion):
| Feld | Regel |
|------|-------|
| action.type | ∈ {hold, add, trim, exit} |
| action.target_w | Pflicht für add/trim; verboten ≠0 bei exit; ≥0 wenn vorhanden |
| action.ttl_days | ≥1 wenn vorhanden |
| confidence | float ∈ [0,1] |
| status | initial 'draft'; nur Übergänge draft→proposed→approved|rejected |
| reviewers | Liste Strings; Reviewer beim Transition hinzugefügt |
| expires_at | approved_at + ttl_days (falls action.ttl_days gesetzt) |

Workflow API:
`transition_status(card, new_status, reviewer=None, now=None)` → Mutiert Karte mit obigen Constraints.

Audit Trail (Geplant):
- Nächster Schritt: Historisierung jeder Transition (timestamp, from→to, reviewer) für Revisionssicherheit.

Status: SPEZIFIKATION AKTUALISIERT – alle dargestellten Felder implementiert, Audit Trail offen.

Siehe Roadmap für Governance-Erweiterungen & DecisionCard Dashboard Plan.
