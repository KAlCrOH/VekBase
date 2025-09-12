# Data Schema — trades.csv

Required columns:
- trade_id (string, unique)
- ts (ISO datetime, lokal)
- ticker (string, e.g., NVDA)
- action (BUY|SELL)
- shares (float > 0)
- price (float >= 0)
- fees (float >= 0, default 0)

Optional columns:
- tag (string; e.g., AI, Defense)
- note_path (relative path to data/notes/*.md)
- account (string; optional)

Validation:
- SELL darf Shares einer Position nicht negativ machen.
- Preise > 0, Shares > 0, Zeit monotone Ordnung pro trade_id (implementiert per Ticker-Zeitprüfung).
