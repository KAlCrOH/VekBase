from __future__ import annotations

from openai import OpenAI

from src.app.core.config import settings


class LLMClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None, model: str | None = None):
        self.base_url = base_url or settings.openai_base_url
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def chat(self, messages: list[dict]) -> str:
        resp = self.client.chat.completions.create(model=self.model, messages=messages)
        return resp.choices[0].message.content or ""
