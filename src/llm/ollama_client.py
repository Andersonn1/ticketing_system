"""Ollama LLM Client."""

from __future__ import annotations

import json
from functools import lru_cache
from time import perf_counter
from typing import Any

from loguru import logger
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
        started_at = perf_counter()
        logger.debug("Requesting embedding from model {}.", self._embedding_model)
        response = await self._client.embed(model=self._embedding_model, input=text)
        embeddings = response.get("embeddings", [])
        if not embeddings:
            logger.warning("Embedding model {} returned no embeddings.", self._embedding_model)
            raise OllamaResponseError("Ollama returned no embeddings")
        vector = [float(value) for value in embeddings[0]]
        logger.debug(
            "Received embedding from model {} with {} dimensions in {:.2f}s.",
            self._embedding_model,
            len(vector),
            perf_counter() - started_at,
        )
        return vector

    async def chat_json(self, prompt: str, *, system_prompt: str = SYSTEM_PROMPT) -> TriageResultSchema:
        """Generate a structured triage response."""
        started_at = perf_counter()
        logger.debug("Requesting structured chat response from model {}.", self._chat_model)
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
        result = TriageResultSchema.model_validate(payload)
        logger.debug(
            "Received structured chat response from model {} in {:.2f}s.",
            self._chat_model,
            perf_counter() - started_at,
        )
        return result

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
            logger.warning("Unable to parse structured JSON response from Ollama.")
            raise OllamaResponseError("Ollama returned invalid JSON") from exc

        if not isinstance(payload, dict):
            logger.warning("Ollama returned a structured payload that is not a JSON object.")
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
