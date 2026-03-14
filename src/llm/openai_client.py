"""OpenAI LLM client."""

from __future__ import annotations

import json
from functools import lru_cache
from time import perf_counter
from typing import Any, Final, Literal

from loguru import logger
from openai import AsyncOpenAI
from pydantic import ValidationError

from src.core.settings import get_settings
from src.llm.prompt import SYSTEM_PROMPT
from src.schemas import TriageResultSchema

OPENAI_PROVIDER_NAME: Final[Literal["openai"]] = "openai"
OPENAI_EMBEDDING_DIMENSIONS: Final[int] = 1536


class OpenAIClientError(RuntimeError):
    """Raised when an OpenAI request fails in a known way."""

    pass


class OpenAIResponseError(ValueError):
    """Raised when OpenAI returns an invalid payload."""

    pass


def _build_async_openai(*, api_key: str, timeout_seconds: float, max_retries: int) -> AsyncOpenAI:
    """Build the async OpenAI SDK client lazily."""

    return AsyncOpenAI(
        api_key=api_key,
        timeout=timeout_seconds,
        max_retries=max_retries,
    )


def _openai_exception_types() -> tuple[type[Exception], ...]:
    """Load OpenAI exception classes lazily for runtime mapping."""
    from openai import (
        APIConnectionError,
        APITimeoutError,
        AuthenticationError,
        BadRequestError,
        InternalServerError,
        RateLimitError,
    )

    return (
        AuthenticationError,
        RateLimitError,
        APITimeoutError,
        APIConnectionError,
        BadRequestError,
        InternalServerError,
    )


class OpenAIClient:
    """OpenAI-backed client for embeddings and structured triage."""

    __slots__ = ("_chat_model", "_client", "_embedding_dimensions", "_embedding_model")

    def __init__(
        self,
        *,
        api_key: str,
        chat_model: str,
        embedding_model: str,
        timeout_seconds: float,
        max_retries: int,
    ) -> None:
        self._client = _build_async_openai(
            api_key=api_key,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
        self._chat_model = chat_model
        self._embedding_model = embedding_model
        self._embedding_dimensions = OPENAI_EMBEDDING_DIMENSIONS

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""
        (
            authentication_error,
            rate_limit_error,
            api_timeout_error,
            api_connection_error,
            bad_request_error,
            internal_server_error,
        ) = _openai_exception_types()
        started_at = perf_counter()
        logger.debug(
            "Requesting embedding from provider {} using model {}.",
            OPENAI_PROVIDER_NAME,
            self._embedding_model,
        )
        try:
            response = await self._client.embeddings.create(
                model=self._embedding_model,
                input=text,
                encoding_format="float",
            )
            vector = self._extract_embedding(response)
            logger.debug(
                "Received embedding from provider {} model {} with {} dimensions in {:.2f}s. Request ID: {}.",
                OPENAI_PROVIDER_NAME,
                self._embedding_model,
                len(vector),
                perf_counter() - started_at,
                self._extract_request_id(response) or "n/a",
            )
            return vector
        except authentication_error as exc:
            raise self._raise_provider_error("embedding", self._embedding_model, "authentication failed", exc) from exc
        except rate_limit_error as exc:
            raise self._raise_provider_error("embedding", self._embedding_model, "rate limit exceeded", exc) from exc
        except api_timeout_error as exc:
            raise self._raise_provider_error("embedding", self._embedding_model, "request timed out", exc) from exc
        except api_connection_error as exc:
            raise self._raise_provider_error("embedding", self._embedding_model, "connection failed", exc) from exc
        except bad_request_error as exc:
            raise self._raise_provider_error("embedding", self._embedding_model, "request was invalid", exc) from exc
        except internal_server_error as exc:
            raise self._raise_provider_error("embedding", self._embedding_model, "server error", exc) from exc

    async def chat_json(self, prompt: str, *, system_prompt: str = SYSTEM_PROMPT) -> TriageResultSchema:
        """Generate a structured triage response."""
        (
            authentication_error,
            rate_limit_error,
            api_timeout_error,
            api_connection_error,
            bad_request_error,
            internal_server_error,
        ) = _openai_exception_types()
        started_at = perf_counter()
        logger.debug(
            "Requesting structured chat response from provider {} using model {}.",
            OPENAI_PROVIDER_NAME,
            self._chat_model,
        )
        try:
            response = await self._request_structured_response(prompt, system_prompt=system_prompt)
        except authentication_error as exc:
            raise self._raise_provider_error("triage", self._chat_model, "authentication failed", exc) from exc
        except rate_limit_error as exc:
            raise self._raise_provider_error("triage", self._chat_model, "rate limit exceeded", exc) from exc
        except api_timeout_error as exc:
            raise self._raise_provider_error("triage", self._chat_model, "request timed out", exc) from exc
        except api_connection_error as exc:
            raise self._raise_provider_error("triage", self._chat_model, "connection failed", exc) from exc
        except bad_request_error as exc:
            raise self._raise_provider_error("triage", self._chat_model, "request was invalid", exc) from exc
        except internal_server_error as exc:
            raise self._raise_provider_error("triage", self._chat_model, "server error", exc) from exc

        try:
            payload = self._load_json_payload(self._extract_output_text(response))
            result = TriageResultSchema.model_validate(payload)
        except (OpenAIResponseError, ValidationError):
            logger.warning(
                "Structured triage response from model {} was invalid; retrying once. Request ID: {}.",
                self._chat_model,
                self._extract_request_id(response) or "n/a",
            )
            recovery_response = await self._request_structured_response(
                f"{prompt}\n\nThe last response was invalid. Return only JSON that exactly matches the schema.",
                system_prompt=system_prompt,
            )
            try:
                payload = self._load_json_payload(self._extract_output_text(recovery_response))
                result = TriageResultSchema.model_validate(payload)
                response = recovery_response
            except (OpenAIResponseError, ValidationError) as recovery_exc:
                raise OpenAIResponseError("OpenAI returned invalid structured triage output") from recovery_exc
        logger.debug(
            "Received structured chat response from provider {} model {} in {:.2f}s. Request ID: {}.",
            OPENAI_PROVIDER_NAME,
            self._chat_model,
            perf_counter() - started_at,
            self._extract_request_id(response) or "n/a",
        )
        return result

    async def _request_structured_response(self, prompt: str, *, system_prompt: str) -> Any:
        """Request strict JSON-schema output from OpenAI."""
        return await self._client.responses.create(
            model=self._chat_model,
            instructions=system_prompt,
            input=prompt,
            temperature=0,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "ticket_triage",
                    "schema": TriageResultSchema.model_json_schema(),
                    "strict": True,
                }
            },
        )

    @staticmethod
    def _load_json_payload(content: Any) -> dict[str, Any]:
        """Parse a JSON object from the OpenAI response payload."""
        if isinstance(content, dict):
            return content

        if not isinstance(content, str):
            logger.warning("OpenAI returned an unsupported structured payload type.")
            raise OpenAIResponseError("OpenAI returned an unsupported response payload")

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            logger.warning("Unable to parse structured JSON response from OpenAI.")
            raise OpenAIResponseError("OpenAI returned invalid JSON") from exc

        if not isinstance(payload, dict):
            logger.warning("OpenAI returned a structured payload that is not a JSON object.")
            raise OpenAIResponseError("OpenAI JSON payload must be an object")
        return payload

    @classmethod
    def _extract_output_text(cls, response: Any) -> str:
        """Extract text content from an OpenAI response object."""
        output_text = cls._read_field(response, "output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text

        output_items = cls._read_field(response, "output")
        if isinstance(output_items, list):
            parts: list[str] = []
            for item in output_items:
                if cls._read_field(item, "type") != "message":
                    continue
                content_items = cls._read_field(item, "content")
                if not isinstance(content_items, list):
                    continue
                for part in content_items:
                    if cls._read_field(part, "type") != "output_text":
                        continue
                    text = cls._read_field(part, "text")
                    if isinstance(text, str) and text:
                        parts.append(text)
            if parts:
                return "".join(parts)

        logger.warning("OpenAI returned no structured text output.")
        raise OpenAIResponseError("OpenAI returned no output text")

    def _extract_embedding(self, response: Any) -> list[float]:
        """Extract one embedding vector from an OpenAI response object."""
        data = self._read_field(response, "data")
        if not isinstance(data, list) or not data:
            logger.warning("Embedding model {} returned no embedding data.", self._embedding_model)
            raise OpenAIResponseError("OpenAI returned no embeddings")

        embedding = self._read_field(data[0], "embedding")
        if not isinstance(embedding, list) or not embedding:
            logger.warning("Embedding model {} returned an empty embedding.", self._embedding_model)
            raise OpenAIResponseError("OpenAI returned no embeddings")

        vector = [float(value) for value in embedding]
        if len(vector) != self._embedding_dimensions:
            logger.warning(
                "Embedding model {} returned {} dimensions instead of {}.",
                self._embedding_model,
                len(vector),
                self._embedding_dimensions,
            )
            raise OpenAIResponseError("OpenAI returned an embedding with the wrong dimensions")
        return vector

    @classmethod
    def _extract_request_id(cls, value: Any) -> str | None:
        """Extract the OpenAI request ID from a response or exception."""
        for field_name in ("_request_id", "request_id"):
            candidate = cls._read_field(value, field_name)
            if isinstance(candidate, str) and candidate:
                return candidate

        headers = cls._read_field(value, "headers")
        if isinstance(headers, dict):
            candidate = headers.get("x-request-id")
            if isinstance(candidate, str) and candidate:
                return candidate

        response = cls._read_field(value, "response")
        if response is not None and response is not value:
            return cls._extract_request_id(response)
        return None

    def _raise_provider_error(self, operation: str, model: str, message: str, exc: Exception) -> OpenAIClientError:
        """Raise a sanitized provider-specific exception after logging."""
        request_id = self._extract_request_id(exc) or "n/a"
        logger.warning(
            "OpenAI {} request failed for model {}: {}. Request ID: {}.",
            operation,
            model,
            message,
            request_id,
        )
        return OpenAIClientError(f"OpenAI {operation} request {message}")

    @staticmethod
    def _read_field(value: Any, field_name: str) -> Any:
        """Read a field from either an SDK object or a plain dict."""
        if isinstance(value, dict):
            return value.get(field_name)
        return getattr(value, field_name, None)


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAIClient:
    """Build a cached OpenAI client from application settings."""
    settings = get_settings()
    api_key = settings.openai_api_key
    if not api_key.get_secret_value().strip():
        raise ValueError("OPENAI_API_KEY is required to build the OpenAI client")

    return OpenAIClient(
        api_key=api_key.get_secret_value(),
        chat_model=settings.openai_chat_model,
        embedding_model=settings.openai_embedding_model,
        timeout_seconds=settings.openai_timeout_seconds,
        max_retries=settings.openai_max_retries,
    )
