"""Async Ollama client tests."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock

from src.llm.ollama_client import OllamaClient, OllamaResponseError


class OllamaClientTests(unittest.IsolatedAsyncioTestCase):
    """Verify JSON parsing and schema validation."""

    async def test_chat_json_parses_fenced_json(self) -> None:
        client = OllamaClient(
            host="http://localhost:11434",
            chat_model="qwen3.5:2b",
            embedding_model="nomic-embed-text",
        )
        client._client.chat = AsyncMock(
            return_value={
                "message": {
                    "content": """```json
                        {"category":"software",
                        "priority":"medium",
                        "summary":"Summary",
                        "response":"Response",
                        "next_steps":["Step 1"],"confidence":"high"
                        }
                        ```"""
                }
            }
        )

        result = await client.chat_json("prompt")

        self.assertEqual(result.category.value, "software")
        self.assertEqual(result.confidence.value, "high")

    async def test_chat_json_rejects_invalid_json(self) -> None:
        client = OllamaClient(
            host="http://localhost:11434",
            chat_model="qwen3.5:2b",
            embedding_model="nomic-embed-text",
        )
        client._client.chat = AsyncMock(return_value={"message": {"content": "not json"}})

        with self.assertRaises(OllamaResponseError):
            await client.chat_json("prompt")


if __name__ == "__main__":
    unittest.main()
