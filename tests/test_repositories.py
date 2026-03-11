"""Repository behavior tests with mocked async sessions."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from src.repositories.kb_chunk_repository import KBChunkRepository
from src.repositories.ticket_embedding_repository import TicketEmbeddingRepository


class FakeMappingsResult:
    """Minimal SQLAlchemy mappings result stand in."""

    def __init__(self, rows: list[dict[str, object]]) -> None:
        self._rows = rows

    def all(self) -> list[dict[str, object]]:
        return self._rows


class FakeExecuteResult:
    """Minimal SQLAlchemy execute result stand in."""

    def __init__(self, rows: object) -> None:
        self._rows = rows

    def mappings(self) -> FakeMappingsResult:
        if not isinstance(self._rows, list):
            raise TypeError("Expected list rows for mappings()")
        return FakeMappingsResult(self._rows)

    def scalar_one_or_none(self) -> object:
        return self._rows


class RepositoryTests(unittest.IsolatedAsyncioTestCase):
    """Exercise repository helpers without a live database."""

    async def test_kb_search_maps_rows_to_schema(self) -> None:
        kb_rows: list[dict[str, object]] = [
            {
                "id": 1,
                "source_name": "password_reset_policy",
                "chunk_text": "Wait 15 minutes.",
                "metadata": {"category": "authentication"},
                "similarity": 0.91,
            }
        ]
        session = MagicMock()
        session.execute = AsyncMock(return_value=FakeExecuteResult(kb_rows))
        repository = KBChunkRepository(session)

        result = await repository.search_similar([0.1, 0.2], top_k=3)

        self.assertEqual(result[0].source_name, "password_reset_policy")
        self.assertAlmostEqual(result[0].similarity, 0.91)

    async def test_ticket_embedding_upsert_updates_existing_row(self) -> None:
        existing = SimpleNamespace(ticket_id=7, combined_text="old", embedding=[0.1])
        session = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        repository = TicketEmbeddingRepository(session)
        repository.get_by_ticket_id = AsyncMock(return_value=existing)

        result = await repository.upsert(
            ticket_id=7,
            combined_text="new text",
            embedding=[0.4, 0.5],
        )

        self.assertEqual(result.combined_text, "new text")
        self.assertEqual(result.embedding, [0.4, 0.5])
        session.flush.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
