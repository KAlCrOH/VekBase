from __future__ import annotations

from pathlib import Path
from typing import Iterable


def iter_text_files(root: str | Path) -> Iterable[Path]:
    p = Path(root)
    for path in p.glob("**/*.txt"):
        if path.is_file():
            yield path


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")
