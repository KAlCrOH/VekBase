# Dev Manifesto

Coding values: Klarheit > Cleverness. Kleine Module, reine Funktionen wo möglich, explizite Seiteneffekte.

Invariants:
- Keine versteckte I/O in Analytics.
- Rechenlogik in `core/*`, UI ist dünn.
- Daten liegen in `data/`, nie in `app/`.
 - `pytest.ini` definiert Pfad statt sys.path Hacks.
 - Frontend-first: zentrale Streamlit Konsole dient auch als Developer-Oberfläche (Tests, später Lints) ohne Business-Logik zu enthalten.

Repro:
- Jede Simulation schreibt Hash/Seed/Params nach `data/results/`.
- Schema-Änderungen dokumentiert in `CONTEXT/04_DATA_SCHEMA_TRADES.md`.

Performance:
- DuckDB für Aggregationen (optional; noch nicht integriert).
- Geplante Caching-Strategien (Quotes später; keine Embeddings implementiert – RAG optional, siehe Policy).

Testing:
- Smoke-Tests (CSV lesen/schreiben, realized Kennzahlen, kleine Simulation). Unrealized/Pattern Tests folgen Roadmap.
