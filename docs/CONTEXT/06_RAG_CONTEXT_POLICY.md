# RAG Context Policy

Sources: Nur lokale Dateien (data/notes/*, data/cache/*). Keine externen Netzquellen.

Rules (ZIEL):
- Retrieval immer mit (ticker, as_of) filtern.
- Keine Look-ahead-Bias: Dokumente nach as_of tabu.
- Max 8 Chunks, 800-1200 Tokens total.

Ranking (ZIEL):
- Kombination lexical + (optional) embeddings.
- Zeitnähe (publish_date <= as_of) als Boost.

Output (IST): Simple Keyword Count (Snippet). Kein Filter (ticker, as_of) → Backlog P1 Retrieval Filter.
Status: Stub ohne Embeddings; Embeddings/Rerank optional (Roadmap). Keine Netzwerkzugriffe vorgesehen.

Backlog: Retrieval Filter (ticker, as_of) (#3) — siehe tmp_backlogCollection.md
