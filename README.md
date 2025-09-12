# VekBase — Personal Investor Workbench (MVP Scaffold)

## Leitlinien (aus CONTEXT)
- Klarheit vor Cleverness; reine Funktionen bevorzugt; UI bleibt dünn (`app/ui` nur Darstellung).
- Tradeschema (`trades.csv`):
  - Required: trade_id(str, unique), ts(ISO datetime, lokal), ticker(str), action(BUY|SELL), shares(float>0), price(float>=0), fees(float>=0 default 0)
  - Optional: tag(str), note_path(relativ zu `data/notes`), account(str)
  - Validation: SELL darf Position nicht negativ machen; monotone Zeitfolge pro `trade_id`; Preise>0; Shares>0.
- Daten liegen ausschließlich unter `data/`.
- Simulationen: deterministisch über Seed; schreiben Parameter/Seed-Hash nach `data/results/`.
- Keine Look-ahead-Bias (siehe `CONTEXT/06_RAG_CONTEXT_POLICY.md`). RAG ist optional.
- Non-Goals: Broker-Sync, Multi-User, Cloud/MLOps.

## Geplante Module
- `app/core/trade_model.py`: Dataclass + Validation.
- `app/core/trade_repo.py`: In-Memory + CSV Load/Save + Positionsvalidierung.
- `app/analytics/metrics.py`: Basis-Kennzahlen inkl. realized PnL, Win-Rate, Profit-Factor, realized Max Drawdown.
- `app/sim/simple_walk.py`: Einfache Walk-Forward Simulation (Seed-basiert).
- `app/ui/admin.py`: Streamlit Admin Oberfläche.
- `tests/`: Pytests für Schema, Analytics, Simulation Determinismus.

## Setup (lokal)
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Streamlit Start
```
streamlit run app/ui/admin.py
```

## Nächste Schritte
1. Implementierung der Module laut Plan.
2. CSV Beispiel unter `data/trades.csv` hinzufügen (manuell).
3. Erweiterte Analytics (Equity Curve, unrealized PnL, Holding-Dauer, Patterns) & optionale RAG später.

## Lizenz
Persönliche Nutzung (nicht für Enterprise).