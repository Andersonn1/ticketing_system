"""Service layer triage tests."""

from __future__ import annotations

import unittest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

from src.models import (
    AIConfidence,
    ServiceCategory,
    ServicePriority,
    ServiceStatus,
    TicketModel,
    UserRole,
)
from src.schemas import (
    RetrievedKBMatchSchema,
    RetrievedTicketMatchSchema,
    TriageResultSchema,
)
from src.services.contracts import SupportsTriageLLMContract
from src.services.ticket_service import TicketService


class FakeSession:
    """Minimal async session for service tests."""

    def __init__(self) -> None:
        self.commit = AsyncMock()
        self.refresh = AsyncMock()


class ServiceTicketServiceTests(unittest.IsolatedAsyncioTestCase):
    """Verify async ticket triage orchestration."""

    async def asyncSetUp(self) -> None:
        self.fake_session = FakeSession()
        self.fake_ticket = TicketModel(
            id=7,
            requestor_name="Jane Student",
            requestor_email="jane@example.edu",
            user_role=UserRole.STUDENT,
            title="Canvas login issue",
            description="Login fails after reset",
            status=ServiceStatus.OPEN,
            priority=ServicePriority.LOW,
            category=ServiceCategory.OTHER,
            ai_summary=None,
            ai_response=None,
            ai_next_steps=[],
            ai_confidence=None,
            ai_trace=None,
        )

        @asynccontextmanager
        async def fake_get_session():
            yield self.fake_session

        self.fake_get_session = fake_get_session
        self.ticket_repository_patch = patch("src.services.ticket_service.TicketRepository")
        self.kb_repository_patch = patch("src.services.ticket_service.KBChunkRepository")
        self.embedding_repository_patch = patch("src.services.ticket_service.TicketEmbeddingRepository")

        self.ticket_repository_cls = self.ticket_repository_patch.start()
        self.kb_repository_cls = self.kb_repository_patch.start()
        self.embedding_repository_cls = self.embedding_repository_patch.start()

        self.ticket_repository = self.ticket_repository_cls.return_value
        self.kb_repository = self.kb_repository_cls.return_value
        self.embedding_repository = self.embedding_repository_cls.return_value

        self.ticket_repository.get_by_id = AsyncMock(
            side_effect=lambda ticket_id: self.fake_ticket if ticket_id == self.fake_ticket.id else None
        )
        self.ticket_repository.apply_triage = AsyncMock(side_effect=lambda ticket, triage, trace: ticket)
        self.kb_repository.search_similar = AsyncMock(
            return_value=[
                RetrievedKBMatchSchema(
                    id=1,
                    source_name="password_reset_policy",
                    chunk_text="Wait 15 minutes.",
                    metadata={"category": "authentication"},
                    similarity=0.95,
                )
            ]
        )
        self.embedding_repository.search_similar = AsyncMock(
            return_value=[
                RetrievedTicketMatchSchema(
                    ticket_id=11,
                    title="Password reset sync delay",
                    combined_text="Title: Password reset sync delay",
                    similarity=0.9,
                )
            ]
        )
        self.embedding_repository.upsert = AsyncMock()

        self.llm_client = AsyncMock(spec=SupportsTriageLLMContract)
        self.llm_client.embed_text.return_value = [0.1, 0.2, 0.3]
        self.llm_client.chat_json.return_value = TriageResultSchema(
            category=ServiceCategory.SOFTWARE,
            priority=ServicePriority.MEDIUM,
            summary="Summary",
            response="Response",
            next_steps=["Wait 15 minutes"],
            confidence=AIConfidence.HIGH,
        )

    async def asyncTearDown(self) -> None:
        self.embedding_repository_patch.stop()
        self.kb_repository_patch.stop()
        self.ticket_repository_patch.stop()

    async def test_triage_ticket_updates_ticket_and_embedding(self) -> None:
        service = TicketService(
            session_provider=self.fake_get_session,
            ollama_client=self.llm_client,
        )

        result = await service.triage_ticket(7)

        self.assertEqual(result.priority.value, "low")
        self.embedding_repository.search_similar.assert_awaited_once()
        self.embedding_repository.upsert.assert_awaited_once()
        self.fake_session.commit.assert_awaited_once()

    async def test_triage_tickets_collects_failures(self) -> None:
        service = TicketService(
            session_provider=self.fake_get_session,
            ollama_client=self.llm_client,
        )

        result = await service.triage_tickets([7, 999])

        self.assertEqual(result.completed, [7])
        self.assertIn(999, result.failed)


if __name__ == "__main__":
    unittest.main()
