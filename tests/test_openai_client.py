"""Async OpenAI client tests."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from src.llm.openai_client import (
    OPENAI_EMBEDDING_DIMENSIONS,
    OpenAIClient,
    OpenAIClientError,
    OpenAIResponseError,
    _triage_response_schema,
)


class OpenAIClientTests(unittest.IsolatedAsyncioTestCase):
    """Verify OpenAI response parsing and error mapping."""

    def test_triage_response_schema_strips_ref_sibling_keywords(self) -> None:
        schema = _triage_response_schema()

        self.assertEqual(schema["properties"]["category"], {"$ref": "#/$defs/ServiceCategory"})
        self.assertEqual(schema["properties"]["priority"], {"$ref": "#/$defs/ServicePriority"})
        self.assertEqual(schema["properties"]["department"], {"$ref": "#/$defs/ServiceDepartment"})
        self.assertEqual(schema["properties"]["confidence"], {"$ref": "#/$defs/AIConfidence"})

    async def test_chat_json_parses_structured_output(self) -> None:
        fake_sdk_client = SimpleNamespace(
            responses=SimpleNamespace(
                create=AsyncMock(
                    return_value=SimpleNamespace(
                        output_text=(
                            '{"category":"software_issue","priority":"medium","department":"helpdesk",'
                            '"summary":"Summary","recommended_action":"Response","confidence":"high",'
                            '"missing_information":"none","reasoning":"Because the ticket says so."}'
                        ),
                        _request_id="req_triage",
                    )
                )
            ),
            embeddings=SimpleNamespace(create=AsyncMock()),
        )
        with patch("src.llm.openai_client._build_async_openai", return_value=fake_sdk_client):
            client = OpenAIClient(
                api_key="sk-test",
                chat_model="gpt-4o-mini",
                embedding_model="text-embedding-3-small",
                timeout_seconds=60,
                max_retries=2,
            )

        result = await client.chat_json("prompt")

        self.assertEqual(result.category.value, "software_issue")
        self.assertEqual(result.department.value, "helpdesk")
        self.assertEqual(result.confidence.value, "high")
        fake_sdk_client.responses.create.assert_awaited_once()
        _, kwargs = fake_sdk_client.responses.create.await_args
        self.assertEqual(kwargs["text"]["format"]["schema"], _triage_response_schema())

    async def test_chat_json_retries_once_after_invalid_json(self) -> None:
        fake_sdk_client = SimpleNamespace(
            responses=SimpleNamespace(
                create=AsyncMock(
                    side_effect=[
                        SimpleNamespace(output_text="not json"),
                        SimpleNamespace(
                            output_text=(
                                '{"category":"network","priority":"high","department":"network_team",'
                                '"summary":"Summary","recommended_action":"Investigate the access point.",'
                                '"confidence":"high","missing_information":"none",'
                                '"reasoning":"The outage affects multiple users."}'
                            )
                        ),
                    ]
                )
            ),
            embeddings=SimpleNamespace(create=AsyncMock()),
        )
        with patch("src.llm.openai_client._build_async_openai", return_value=fake_sdk_client):
            client = OpenAIClient(
                api_key="sk-test",
                chat_model="gpt-4o-mini",
                embedding_model="text-embedding-3-small",
                timeout_seconds=60,
                max_retries=2,
            )

        result = await client.chat_json("prompt")

        self.assertEqual(result.department.value, "network_team")
        self.assertEqual(fake_sdk_client.responses.create.await_count, 2)

    async def test_chat_json_rejects_invalid_json_after_retry(self) -> None:
        fake_sdk_client = SimpleNamespace(
            responses=SimpleNamespace(
                create=AsyncMock(
                    side_effect=[
                        SimpleNamespace(output_text="not json"),
                        SimpleNamespace(output_text="still not json"),
                    ]
                )
            ),
            embeddings=SimpleNamespace(create=AsyncMock()),
        )
        with patch("src.llm.openai_client._build_async_openai", return_value=fake_sdk_client):
            client = OpenAIClient(
                api_key="sk-test",
                chat_model="gpt-4o-mini",
                embedding_model="text-embedding-3-small",
                timeout_seconds=60,
                max_retries=2,
            )

        with self.assertRaises(OpenAIResponseError):
            await client.chat_json("prompt")

    async def test_embed_text_returns_expected_vector(self) -> None:
        fake_sdk_client = SimpleNamespace(
            responses=SimpleNamespace(create=AsyncMock()),
            embeddings=SimpleNamespace(
                create=AsyncMock(
                    return_value=SimpleNamespace(
                        data=[SimpleNamespace(embedding=[0.5] * OPENAI_EMBEDDING_DIMENSIONS)],
                        _request_id="req_embed",
                    )
                )
            ),
        )
        with patch("src.llm.openai_client._build_async_openai", return_value=fake_sdk_client):
            client = OpenAIClient(
                api_key="sk-test",
                chat_model="gpt-4o-mini",
                embedding_model="text-embedding-3-small",
                timeout_seconds=60,
                max_retries=2,
            )

        result = await client.embed_text("hello")

        self.assertEqual(len(result), OPENAI_EMBEDDING_DIMENSIONS)
        fake_sdk_client.embeddings.create.assert_awaited_once()
        _, kwargs = fake_sdk_client.embeddings.create.await_args
        self.assertNotIn("dimensions", kwargs)

    async def test_embed_text_rejects_empty_embedding(self) -> None:
        fake_sdk_client = SimpleNamespace(
            responses=SimpleNamespace(create=AsyncMock()),
            embeddings=SimpleNamespace(
                create=AsyncMock(return_value=SimpleNamespace(data=[SimpleNamespace(embedding=[])]))
            ),
        )
        with patch("src.llm.openai_client._build_async_openai", return_value=fake_sdk_client):
            client = OpenAIClient(
                api_key="sk-test",
                chat_model="gpt-4o-mini",
                embedding_model="text-embedding-3-small",
                timeout_seconds=60,
                max_retries=2,
            )

        with self.assertRaises(OpenAIResponseError):
            await client.embed_text("hello")

    async def test_chat_json_maps_known_openai_errors(self) -> None:
        class FakeAuthenticationError(Exception):
            pass

        class FakeRateLimitError(Exception):
            pass

        class FakeTimeoutError(Exception):
            pass

        class FakeConnectionError(Exception):
            pass

        class FakeBadRequestError(Exception):
            pass

        class FakeInternalServerError(Exception):
            pass

        exception_types = (
            FakeAuthenticationError,
            FakeRateLimitError,
            FakeTimeoutError,
            FakeConnectionError,
            FakeBadRequestError,
            FakeInternalServerError,
        )
        cases = (
            FakeAuthenticationError("bad key"),
            FakeRateLimitError("slow down"),
            FakeTimeoutError("timeout"),
            FakeConnectionError("offline"),
            FakeBadRequestError("bad request"),
            FakeInternalServerError("server error"),
        )

        for exc in cases:
            with self.subTest(exception_type=type(exc).__name__):
                fake_sdk_client = SimpleNamespace(
                    responses=SimpleNamespace(create=AsyncMock(side_effect=exc)),
                    embeddings=SimpleNamespace(create=AsyncMock()),
                )
                with (
                    patch("src.llm.openai_client._build_async_openai", return_value=fake_sdk_client),
                    patch("src.llm.openai_client._openai_exception_types", return_value=exception_types),
                ):
                    client = OpenAIClient(
                        api_key="sk-test",
                        chat_model="gpt-4o-mini",
                        embedding_model="text-embedding-3-small",
                        timeout_seconds=60,
                        max_retries=2,
                    )

                    with self.assertRaises(OpenAIClientError):
                        await client.chat_json("prompt")


if __name__ == "__main__":
    unittest.main()
