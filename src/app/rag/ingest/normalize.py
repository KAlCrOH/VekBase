from __future__ import annotations

import unicodedata


def normalize_text(text: str) -> str:
    t = unicodedata.normalize("NFC", text)
    t = t.replace("\u00A0", " ")
    t = "\n".join(line.strip() for line in t.splitlines())
    return t.strip()
