# RAG Context Policy

Sources: Nur lokale Dateien (data/notes/*, data/cache/*). Bevorzugt neueste, aber niemals nach as_of Zeit schneiden.

Rules:
- Retrieval immer mit (ticker, as_of) filtern.
- Keine Look-ahead-Bias: Dokumente nach as_of sind tabu.
- Max 8 Chunks, 800-1200 Tokens total.

Ranking:
- Dense (embeddings) ∧ Lexikalisch (BM25 simuliert via ngrams).
- Zeitnähe (publish_date <= as_of) als Boost.

Output: Liste der Pfade + Snippets.
Status: RAG Retrieval und Embeddings nicht implementiert (Planned, optional). Keine Netzwerkzugriffe vorgesehen.
