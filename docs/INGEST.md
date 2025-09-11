# INGEST – Pipeline & Qualität

Ziel: Rohtexte deterministisch in normalisierte, versionierte Chunks überführen, die direkt eingebettet und indexiert werden können – auditierbar & reproduzierbar.

## Pipeline Überblick
1. Discovery: Scan `data/raw/` (aktuell: *.txt)
2. Load: Dateiinhalt lesen (`loaders.py`)
3. Normalize: Unicode NFC, Whitespace squash (`normalize.py`)
4. Split: Token-basierter Split mit Überlappung (`splitters.py`)
5. Chunk ID: Stabil via Hash (Pfad + Offset) (`ids.py`)
6. Persist: SQLite (documents, chunks)
7. (Geplant) Export Parquet: `data/processed/*.parquet`
8. Embedding + Index Build (separat CLI `index`)

## Split-Strategie
- Token-basierter Split (tiktoken)
- Standard: `MAX_CHUNK_TOKENS=350`, Overlap 40
- Ziel: Balance Kontextdichte vs. Wiederholungsrate

## Qualitäts- & Audit-Merkmale
| Aspekt | Mechanismus |
|--------|-------------|
| Determinismus | Stabiler Chunk-ID Hash
| Integrität (geplant) | Speicherung chunk_hash (sha256(content))
| Versionierung | EMB_PIPE_VER (Env) triggert Reindex
| Reproduzierbarkeit | Normalisierungsregeln zentral

## CLI Flow (aktuell)
`ingest` (Stub) lädt txt → normalisiert → split → SQLite Insert (LIMIT für Index Build noch im index CLI)

## Geplante Erweiterungen
| Feature | Nutzen |
|---------|-------|
| Markdown Loader | Strukturreichere Quellen
| PDF Loader | Unternehmensdokumente
| Parquet Export | Schneller Batch-Embed
| MIME Filter | Sicherheit / Konsistenz
| Duplikat-Erkennung | Weniger redundante Vektoren
| Chunk Hash Verify | Integrity beim Retrieval

## Best Practices
- Große Dateien vorab logical section splitten (Überschriften)
- Konsistente Encoding (UTF-8)
- Keine binären Dateien in `data/raw/`

## Nächste Schritte (Priorität)
1. Parquet Export implementieren
2. Hash-Feld in chunks Tabelle
3. PDF / Markdown Loader
4. Embedding Batch Pipeline ohne LIMIT
