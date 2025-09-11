# SETUP GPU (RTX 5090)

## Empfehlung
- WSL2 (Ubuntu 22.04) + NVIDIA CUDA Toolkit
- vLLM als OpenAI-kompatibler Endpoint; Alternativ Ollama lokal
- FAISS GPU via conda (faiss-gpu) oder wheels (wenn verfügbar)

## Schnellanleitung
1. Windows NVIDIA Treiber aktuell
2. WSL2 aktivieren & Ubuntu installieren
3. Test `nvidia-smi` in WSL2
4. Python 3.11 Umgebung erstellen
5. Install: `pip install torch --index-url https://download.pytorch.org/whl/cu121`
6. `pip install sentence-transformers`
7. `conda install -c pytorch -c nvidia faiss-gpu` (oder CPU Variante)
8. vLLM starten (Beispiel unten)
9. `.env` OPENAI_BASE_URL anpassen

## vLLM Beispiel
```
python -m vllm.entrypoints.openai.api_server \
	--model mistralai/Mistral-7B-Instruct-v0.3 \
	--dtype float16 \
	--tensor-parallel-size 1 \
	--port 8001
```
`OPENAI_BASE_URL=http://localhost:8001/v1`

## Ollama Beispiel
```
ollama run llama3.1
```
Oder Modell vorladen und dann Standard OpenAI Pfad nutzen: `http://localhost:11434/v1`

## FAISS GPU Hinweise
- FlatIP: Einfach, GPU Beschleunigung minimal Setup
- IVF: `faiss.index_factory(dim, "IVF1024,Flat", METRIC_INNER_PRODUCT)` + Training Schritt
- HNSW: Build CPU -> ggf. GPU Transfer (später)

## Performance Tuning
| Bereich | Tipp |
|---------|------|
| Embedding | Größere Batch (bis VRAM Limit) |
| Dtype | fp16 embeddings wenn Modell kompatibel |
| Index Persistenz | Speichere auf NVMe |
| Warmup | 1 Dummy Query nach Start |

## Fehlerbehebung
| Problem | Lösung |
|---------|--------|
| `CUDA out of memory` | Batch verkleinern |
| Fehlende GPU Wheels | Auf CPU faiss ausweichen |
| Langsamer Start | Modell quantisieren (später) |

## Roadmap GPU
- Automatische GPU Erkennung
- Mixed Precision Embedding Pipeline
- Quantisierte Indizes für große Korpora
