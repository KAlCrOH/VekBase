from __future__ import annotations

import argparse

from src.app.core.config import settings
from src.app.rag.retrieve.retriever import Retriever


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--query", required=True)
    p.add_argument("--top-k", type=int, default=settings.top_k)
    args = p.parse_args()

    r = Retriever()
    results = r.query(args.query, args.top_k)
    for doc in results:
        print(doc)


if __name__ == "__main__":
    main()
