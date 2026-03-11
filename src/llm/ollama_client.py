"""Ollama LLM Client."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from ollama import AsyncClient

from src.core.settings import get_settings
from src.llm.prompt import SYSTEM_PROMPT
from src.schemas import TriageResultSchema


class OllamaResponseError(ValueError):
    """Raised when Ollama returns invalid structured output."""

    pass


class OllamaClient:
    """Ollama LLM Client"""

    __slots__ = ("_client", "_chat_model", "_embedding_model")

    def __init__(
        self,
        *,
        host: str,
        chat_model: str,
        embedding_model: str,
    ) -> None:
        self._client = AsyncClient(host=host)
        self._chat_model = chat_model
        self._embedding_model = embedding_model

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""
        response = await self._client.embed(model=self._embedding_model, input=text)
        embeddings = response.get("embeddings", [])
        if not embeddings:
            raise OllamaResponseError("Ollama returned no embeddings")
        return [float(value) for value in embeddings[0]]

    async def chat_json(self, prompt: str, *, system_prompt: str = SYSTEM_PROMPT) -> TriageResultSchema:
        """Generate a structured triage response."""
        response = await self._client.chat(
            model=self._chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            format=TriageResultSchema.model_json_schema(),
            options={"temperature": 0},
        )
        message = response.get("message", {})
        content = message.get("content")
        payload = self._load_json_payload(content)
        return TriageResultSchema.model_validate(payload)

    @staticmethod
    def _load_json_payload(content: Any) -> dict[str, Any]:
        """Parse a JSON object from the Ollama chat response."""
        if isinstance(content, dict):
            return content

        if not isinstance(content, str):
            raise OllamaResponseError("Ollama returned an unsupported response payload")

        normalized = content.strip()
        if normalized.startswith("```"):
            normalized = normalized.strip("`")
            if normalized.startswith("json"):
                normalized = normalized[4:].strip()

        try:
            payload = json.loads(normalized)
        except json.JSONDecodeError as exc:
            raise OllamaResponseError("Ollama returned invalid JSON") from exc

        if not isinstance(payload, dict):
            raise OllamaResponseError("Ollama JSON payload must be an object")
        return payload


@lru_cache(maxsize=1)
def get_ollama_client() -> OllamaClient:
    """Build a cached Ollama client from application settings."""
    settings = get_settings()
    return OllamaClient(
        host=settings.ollama_base_url,
        chat_model=settings.chat_model,
        embedding_model=settings.embedding_model,
    )
