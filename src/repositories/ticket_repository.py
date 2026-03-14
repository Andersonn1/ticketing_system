"""Repository for canonical ticket persistence operations."""

from __future__ import annotations

from collections.abc import Sequence

from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ServiceStatus, TicketModel
from src.schemas import (
    ManualTriageSchema,
    TicketAITraceSchema,
    TicketCreateSchema,
    TicketUpdateSchema,
    TriageResultSchema,
)

from .contracts import TicketRepositoryContract


class TicketRepository(TicketRepositoryContract):
    """Async SQLAlchemy repository for ticket records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[TicketModel]:
        """Load all tickets in creation order."""
        result = await self._session.execute(
            select(TicketModel).order_by(TicketModel.created_at.desc(), TicketModel.id.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, ticket_id: int) -> TicketModel | None:
        """Load a single ticket by primary key."""
        result = await self._session.execute(select(TicketModel).where(TicketModel.id == ticket_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, ticket_id: int) -> TicketModel | None:
        """Load and lock a single ticket by primary key for mutation."""
        result = await self._session.execute(select(TicketModel).where(TicketModel.id == ticket_id).with_for_update())
        return result.scalar_one_or_none()

    async def get_by_ids(self, ticket_ids: Sequence[int]) -> list[TicketModel]:
        """Load multiple tickets preserving database ordering."""
        if not ticket_ids:
            return []
        result = await self._session.execute(
            select(TicketModel).where(TicketModel.id.in_(ticket_ids)).order_by(TicketModel.id.asc())
        )
        return list(result.scalars().all())

    async def get_by_business_key(
        self,
        ticket: TicketCreateSchema,
    ) -> TicketModel | None:
        """Load a ticket by stable business fields."""
        result = await self._session.execute(
            select(TicketModel).where(
                and_(
                    TicketModel.requestor_email == ticket.requestor_email,
                    TicketModel.title == ticket.title,
                    TicketModel.description == ticket.description,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create(self, ticket: TicketCreateSchema) -> TicketModel:
        """Insert a new ticket and return a managed row."""
        entity = self._model_from_create(ticket)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def update(
        self,
        ticket: TicketModel,
        payload: TicketCreateSchema | TicketUpdateSchema,
    ) -> TicketModel:
        """Patch an existing row in memory."""
        self._apply_create_payload(ticket, payload)
        await self._session.flush()
        await self._session.refresh(ticket)
        return ticket

    async def claim_for_triage(self, ticket_id: int) -> TicketModel | None:
        """Lock and mark an open ticket as pending so only one triage flow owns it."""
        result = await self._session.execute(
            select(TicketModel)
            .where(
                TicketModel.id == ticket_id,
                TicketModel.status == ServiceStatus.OPEN,
            )
            .with_for_update(skip_locked=True)
        )
        ticket = result.scalar_one_or_none()
        if ticket is None:
            return None

        ticket.status = ServiceStatus.PENDING
        await self._session.flush()
        await self._session.refresh(ticket)
        return ticket

    async def set_status(self, ticket: TicketModel, status: ServiceStatus) -> TicketModel:
        """Persist a status-only transition."""
        ticket.status = status
        await self._session.flush()
        await self._session.refresh(ticket)
        return ticket

    async def apply_triage(
        self,
        ticket: TicketModel,
        triage: TriageResultSchema,
        trace: TicketAITraceSchema,
        processing_ms: int,
    ) -> TicketModel:
        """Persist AI triage fields onto a ticket."""
        logger.info(
            "Persisting AI triage output for ticket {} with category {}, priority {}, and department {}.",
            ticket.id,
            triage.category,
            triage.priority,
            triage.department,
        )
        ticket.category = triage.category
        ticket.priority = triage.priority
        ticket.department = triage.department
        ticket.ai_summary = triage.summary
        ticket.ai_recommended_action = triage.recommended_action
        ticket.ai_missing_information = triage.missing_information
        ticket.ai_reasoning = triage.reasoning
        ticket.ai_processing_ms = processing_ms
        ticket.ai_confidence = triage.confidence
        ticket.ai_trace = trace.model_dump(mode="json")
        await self._session.flush()
        await self._session.refresh(ticket)
        logger.debug("Persisted AI triage output for ticket {}.", ticket.id)
        return ticket

    async def apply_manual_triage(
        self,
        ticket: TicketModel,
        payload: ManualTriageSchema,
    ) -> TicketModel:
        """Persist helpdesk-authored triage output onto a ticket."""
        logger.info(
            "Persisting manual triage output for ticket {} with category {} and priority {}.",
            ticket.id,
            payload.category,
            payload.priority,
        )
        ticket.manual_summary = payload.summary
        ticket.manual_response = payload.response
        ticket.manual_next_steps = payload.next_steps
        ticket.priority = payload.priority
        ticket.category = payload.category
        ticket.status = payload.status
        await self._session.flush()
        await self._session.refresh(ticket)
        logger.debug("Persisted manual triage output for ticket {}.", ticket.id)
        return ticket

    async def delete(self, ticket_id: int) -> bool:
        """Delete a ticket by ID and report whether a row was removed."""
        row = await self._session.get(TicketModel, ticket_id)
        if row is None:
            return False

        await self._session.delete(row)
        return True

    async def bulk_delete(self, ticket_ids: Sequence[int]) -> int:
        """Delete tickets by ID and return the number of affected rows."""
        if not ticket_ids:
            return 0

        rows = list(
            (await self._session.execute(select(TicketModel).where(TicketModel.id.in_(ticket_ids)))).scalars().all()
        )
        for row in rows:
            await self._session.delete(row)

        return len(rows)

    @staticmethod
    def _model_from_create(ticket: TicketCreateSchema) -> TicketModel:
        return TicketModel(
            requestor_name=ticket.requestor_name,
            requestor_email=ticket.requestor_email,
            user_role=ticket.user_role,
            title=ticket.title,
            description=ticket.description,
        )

    @staticmethod
    def _apply_create_payload(entity: TicketModel, payload: TicketCreateSchema | TicketUpdateSchema) -> None:
        entity.requestor_name = payload.requestor_name
        entity.requestor_email = payload.requestor_email
        entity.user_role = payload.user_role
        entity.title = payload.title
        entity.description = payload.description
        if isinstance(payload, TicketUpdateSchema):
            if payload.status is not None:
                entity.status = payload.status
            if payload.priority is not None:
                entity.priority = payload.priority
            if payload.category is not None:
                entity.category = payload.category
