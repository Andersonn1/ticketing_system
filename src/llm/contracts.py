"""LLM Contracts"""

from __future__ import annotations

from typing import Any, Protocol

from src.llm.prompt import SYSTEM_PROMPT
from src.schemas import TriageResultSchema


class OllamaClientContract(Protocol):
    """Ollama LL Client Contract"""

    __slots__ = ("_client", "_chat_model", "_embedding_model")

    def __init__(
        self,
        *,
        host: str,
        chat_model: str,
        embedding_model: str,
    ) -> None: ...

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""
        ...

    async def chat_json(self, prompt: str, *, system_prompt: str = SYSTEM_PROMPT) -> TriageResultSchema:
        """Generate a structured triage response."""
        ...

    @staticmethod
    def _load_json_payload(content: Any) -> dict[str, Any]:
        """Parse a JSON object from the Ollama chat response."""
        ...
