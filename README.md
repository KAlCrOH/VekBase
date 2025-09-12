# VekBase — Personal Investor Workbench (MVP Scaffold)

![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg) <!-- Replace OWNER/REPO nach GitHub Push -->

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

## Implementierte / Neue Module
- `app/core/trade_model.py`: Dataclass + Validation.
- `app/core/trade_repo.py`: In-Memory + CSV Load/Save + Positionsvalidierung.
- `app/analytics/metrics.py`: Realized + Unrealized PnL, Win-Rate, Profit-Factor, realized Max Drawdown, Holding-Dauer (avg), Equity Curve (realized).
- `app/sim/simple_walk.py`: Deterministische Walk-Forward Simulation + `run_and_persist` -> `data/results/<ts>_<hash>/` mit `meta.json` & `equity.csv`.
- `app/core/decision_card.py`: DecisionCard Skeleton.
- `app/core/retrieval.py`: Einfache lokale Keyword Retrieval Stub (RAG Vorbereitung).
- `app/ui/console.py`: Zentrale Streamlit Konsole (Tabs: Trades, Analytics, Simulation Runs (Persistenz), DevTools Test Runner).
- `tests/`: 10+ Pytests (Model, Repo Roundtrip, Analytics, Equity Curve, Simulation, Persistenz, DecisionCard, Retrieval).

## Setup (lokal)
Variante A (klassisch `requirements.txt`):
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Variante B (neu: Packaging via `pyproject.toml`, editable):
```
python -m venv .venv
.venv\Scripts\activate
pip install -U pip
pip install -e .[dev]
```
Damit ist das Paket `vekbase` (Namespace `app`) importierbar ohne Bootstrap.

## Start (Frontend Zentrale)
Editable Install vorausgesetzt (oder Variante A mit Root als CWD):
```
streamlit run app/ui/console.py
```

Admin (Legacy) Ansicht:
```
streamlit run app/ui/admin.py
```

Falls vor editable Installation ausgeführt, sorgt Bootstrap in den UI-Skripten für `sys.path` Anpassung.

## Nächste Schritte
1. Optionale Pattern-Analytics (Histogramme, Scatter) & erweiterte Metriken (CAGR etc.).
2. Ausbau Simulation Parameter (TP/SL, Kostenmodell) + Snapshot Tests.
3. DecisionCard UI Integration + Retrieval Panel.
4. (Optional) Live Quotes Feed (lokal Mock) für fortlaufende unrealized Updates.

## CI
Automatischer Lauf von `pytest -q` über GitHub Actions (`.github/workflows/ci.yml`). Artefakte: `data/devtools/**` (Queue Logs / Snapshots) werden bei jedem Run (immer) hochgeladen. Badge oben aktualisieren nach GitHub Repository Import (`OWNER/REPO` ersetzen).

## Lizenz
Persönliche Nutzung (nicht für Enterprise).