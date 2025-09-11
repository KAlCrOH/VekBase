from __future__ import annotations

SYSTEM_DEFAULT = (
    "Du bist ein hilfsbereiter Assistent. Nutze den bereitgestellten Kontext, antworte präzise."
)

USER_TEMPLATE = (
    "Frage: {query}\n\nKontext:\n{context}\n\nAntworte knapp und beziehe dich auf den Kontext."
)


def build_prompt(query: str, context: str, system: str | None = None) -> list[dict]:
    sys = system or SYSTEM_DEFAULT
    user = USER_TEMPLATE.format(query=query, context=context)
    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": user},
    ]
