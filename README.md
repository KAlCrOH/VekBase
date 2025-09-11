# VekBase – Local-first RAG (FAISS)

Puristisches RAG-Gerüst für lokale Entwicklung mit FAISS, FastAPI, Pydantic, structlog und OpenAI-kompatiblen LLMs (vLLM/Ollama/DeepSeek via base_url). Ziel: Verständliche Basis, später erweiterbar (Agenten, Reranking, Evaluierung).

## Quickstart (Windows PowerShell)
1) venv
```powershell
py -3.11 -m venv .venv ; .\.venv\Scripts\Activate.ps1
```
2) Install
```powershell
python -m pip install -U pip ; pip install -e .[dev]
```
3) .env
Kopiere `.env.example` nach `.env` und passe Variablen an (Index-Pfade, Modelle, base_url).

4) Server
```powershell
uvicorn src.server:app --reload --port 8000
```

5) Test
```powershell
curl -s http://127.0.0.1:8000/health
```

Weitere Infos: `docs/README.md`, `docs/ARCHITECTURE.md`, `docs/USAGE.md`, `docs/SETUP_GPU.md`.
