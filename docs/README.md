# VekBase – Local-first RAG (FAISS + OpenAI-kompatibel)

Ziel: Puristische, modulare Codebasis als Fundament für RAG + spätere Agenten-Orchestrierung.

- Python 3.11+
- FAISS (Index), SQLite/Parquet (Metadaten/Bundles)
- FastAPI, Pydantic, structlog, OpenTelemetry
- OpenAI-kompatible LLMs (vLLM, Ollama, DeepSeek via base_url)

## Quickstart (Windows PowerShell)
1) venv erstellen
```powershell
py -3.11 -m venv .venv ; .\.venv\Scripts\Activate.ps1
```
2) Abhängigkeiten installieren
```powershell
python -m pip install -U pip ; pip install -e .[dev]
```
3) .env aus `.env.example` kopieren und anpassen
4) Dev-Server starten
```powershell
uvicorn src.server:app --reload --port 8000
```

Mehr: `docs/ARCHITECTURE.md`, `docs/USAGE.md`, `docs/SETUP_GPU.md`.
