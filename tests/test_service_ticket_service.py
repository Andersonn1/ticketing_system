"""Service layer triage tests."""

from __future__ import annotations

import unittest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from src.models import (
    AIConfidence,
    ServiceCategory,
    ServicePriority,
    ServiceStatus,
    TicketModel,
    UserRole,
)
from src.schemas import (
    ManualTriageSchema,
    RetrievedKBMatchSchema,
    RetrievedTicketMatchSchema,
    TicketUpdateSchema,
    TriageResultSchema,
)
from src.services.contracts import SupportsTriageLLMContract
from src.services.ticket_service import TicketService


class FakeSession(MagicMock):
    """Minimal async session for service tests."""

    def __init__(self) -> None:
        self.commit = AsyncMock()
        self.refresh = AsyncMock()
        self.rollback = AsyncMock()


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
            manual_summary=None,
            manual_response=None,
            manual_next_steps=[],
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
        self.ticket_repository.get_by_id_for_update = AsyncMock(
            side_effect=lambda ticket_id: self.fake_ticket if ticket_id == self.fake_ticket.id else None
        )
        self.ticket_repository.claim_for_triage = AsyncMock(side_effect=self._claim_for_triage)
        self.ticket_repository.set_status = AsyncMock(
            side_effect=lambda ticket, status: setattr(ticket, "status", status)
        )
        self.ticket_repository.apply_triage = AsyncMock(side_effect=lambda ticket, triage, trace: ticket)
        self.ticket_repository.apply_manual_triage = AsyncMock(side_effect=self._apply_manual_triage)
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

    def _claim_for_triage(self, ticket_id: int) -> TicketModel | None:
        if ticket_id != self.fake_ticket.id or self.fake_ticket.status != ServiceStatus.OPEN:
            return None
        self.fake_ticket.status = ServiceStatus.PENDING
        return self.fake_ticket

    def _apply_manual_triage(self, ticket: TicketModel, payload: ManualTriageSchema) -> TicketModel:
        ticket.manual_summary = payload.summary
        ticket.manual_response = payload.response
        ticket.manual_next_steps = payload.next_steps
        ticket.priority = payload.priority
        ticket.category = payload.category
        ticket.status = payload.status
        return ticket

    async def asyncTearDown(self) -> None:
        self.embedding_repository_patch.stop()
        self.kb_repository_patch.stop()
        self.ticket_repository_patch.stop()

    async def test_triage_ticket_updates_ticket_and_embedding(self) -> None:
        service = TicketService(
            session_provider=self.fake_get_session,
            llm_client=self.llm_client,
        )

        result = await service.triage_ticket(7)

        self.assertEqual(result.status, ServiceStatus.CLOSED)
        self.assertEqual(result.priority.value, "low")
        self.ticket_repository.claim_for_triage.assert_awaited_once_with(7)
        self.ticket_repository.set_status.assert_awaited()
        self.embedding_repository.search_similar.assert_awaited_once()
        self.embedding_repository.upsert.assert_awaited_once()
        self.assertEqual(self.fake_session.commit.await_count, 2)

    async def test_triage_tickets_collects_failures(self) -> None:
        service = TicketService(
            session_provider=self.fake_get_session,
            llm_client=self.llm_client,
        )

        result = await service.triage_tickets([7, 999])

        self.assertEqual(result.completed, [7])
        self.assertIn(999, result.failed)

    async def test_triage_ticket_raises_for_missing_ticket(self) -> None:
        service = TicketService(
            session_provider=self.fake_get_session,
            llm_client=self.llm_client,
        )

        with self.assertRaisesRegex(ValueError, "Ticket 999 was not found"):
            await service.triage_ticket(999)

    async def test_triage_ticket_rejects_ticket_already_pending(self) -> None:
        self.fake_ticket.status = ServiceStatus.PENDING
        service = TicketService(
            session_provider=self.fake_get_session,
            llm_client=self.llm_client,
        )

        with self.assertRaisesRegex(ValueError, "already being triaged"):
            await service.triage_ticket(7)

    async def test_update_ticket_rejects_manual_change_while_pending(self) -> None:
        self.fake_ticket.status = ServiceStatus.PENDING
        service = TicketService(
            session_provider=self.fake_get_session,
            llm_client=self.llm_client,
        )

        with self.assertRaisesRegex(ValueError, "currently being triaged"):
            await service.update_ticket(
                7,
                self._update_payload(status=ServiceStatus.CLOSED),
            )

    async def test_manual_triage_ticket_saves_manual_fields_for_open_ticket(self) -> None:
        service = TicketService(
            session_provider=self.fake_get_session,
            llm_client=self.llm_client,
        )

        result = await service.manual_triage_ticket(7, self._manual_triage_payload(status=ServiceStatus.PENDING))
        assert result is not None
        self.assertEqual(result.status, ServiceStatus.PENDING)
        self.assertEqual(result.manual_summary, "Investigated Canvas login sync issue.")
        self.assertEqual(result.manual_response, "We advised the student to wait for the sync delay to clear.")
        self.assertEqual(result.manual_next_steps, ["Wait 15 minutes.", "Retry Canvas after clearing cache."])
        self.ticket_repository.apply_manual_triage.assert_awaited_once()
        self.fake_session.commit.assert_awaited()

    async def test_manual_triage_ticket_allows_pending_ticket_to_be_resaved(self) -> None:
        self.fake_ticket.status = ServiceStatus.PENDING
        service = TicketService(
            session_provider=self.fake_get_session,
            llm_client=self.llm_client,
        )

        result = await service.manual_triage_ticket(7, self._manual_triage_payload(status=ServiceStatus.CLOSED))
        assert result is not None
        self.assertEqual(result.status, ServiceStatus.CLOSED)
        self.assertEqual(result.priority, ServicePriority.MEDIUM)
        self.assertEqual(result.category, ServiceCategory.SOFTWARE)

    async def test_manual_triage_ticket_rejects_closed_ticket(self) -> None:
        self.fake_ticket.status = ServiceStatus.CLOSED
        service = TicketService(
            session_provider=self.fake_get_session,
            llm_client=self.llm_client,
        )

        with self.assertRaisesRegex(ValueError, "already been closed"):
            await service.manual_triage_ticket(7, self._manual_triage_payload(status=ServiceStatus.CLOSED))

    def _update_payload(self, *, status: ServiceStatus) -> TicketUpdateSchema:
        return TicketUpdateSchema(
            id=self.fake_ticket.id,
            requestor_name=self.fake_ticket.requestor_name,
            requestor_email=self.fake_ticket.requestor_email,
            user_role=self.fake_ticket.user_role,
            title=self.fake_ticket.title,
            description=self.fake_ticket.description,
            status=status,
            priority=self.fake_ticket.priority,
            category=self.fake_ticket.category,
        )

    def _manual_triage_payload(self, *, status: ServiceStatus) -> ManualTriageSchema:
        return ManualTriageSchema(
            summary="Investigated Canvas login sync issue.",
            response="We advised the student to wait for the sync delay to clear.",
            next_steps=["Wait 15 minutes.", "Retry Canvas after clearing cache."],
            priority=ServicePriority.MEDIUM,
            category=ServiceCategory.SOFTWARE,
            status=status,
        )


if __name__ == "__main__":
    unittest.main()
