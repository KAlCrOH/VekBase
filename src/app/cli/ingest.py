from __future__ import annotations

import argparse
from pathlib import Path

from src.app.rag.ingest.splitters import split_by_tokens
from src.app.rag.store.metadata import MetadataStore


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source-dir", default="./data/raw")
    args = p.parse_args()

    m = MetadataStore()
    src = Path(args.source_dir)

    for path in src.glob("**/*.txt"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        chunks = split_by_tokens(text)
        doc_id = m.insert_document(source=str(path), title=path.stem)
        m.insert_chunks(doc_id, [(c, len(c.split())) for c in chunks])
        print(f"Ingested {path} -> {len(chunks)} chunks")


if __name__ == "__main__":
    main()
