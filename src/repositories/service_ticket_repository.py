"""Repository for service ticket persistence operations."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.service_ticket_model import (
    ServiceCategory as ServiceTicketCategory,
)
from src.models.service_ticket_model import (
    ServiceTicketModel,
)
from src.models.service_ticket_model import (
    ServiceUrgency as ServiceTicketUrgency,
)
from src.schemas.service_ticket import ServiceTicketCreate, ServiceTicketUpdate


class ServiceTicketRepository:
    """Async SQLAlchemy repository for ServiceTicket records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[ServiceTicketModel]:
        """Load all tickets in creation order."""
        result = await self._session.execute(
            select(ServiceTicketModel).order_by(ServiceTicketModel.id.asc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, ticket_id: int) -> ServiceTicketModel | None:
        """Load a single ticket by primary key."""
        result = await self._session.execute(
            select(ServiceTicketModel).where(ServiceTicketModel.id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def get_by_business_key(
        self,
        ticket: ServiceTicketCreate,
    ) -> ServiceTicketModel | None:
        """Load a ticket by stable business fields."""
        result = await self._session.execute(
            select(ServiceTicketModel).where(
                and_(
                    ServiceTicketModel.urgency
                    == ServiceTicketUrgency(ticket.urgency.value),
                    ServiceTicketModel.category
                    == ServiceTicketCategory(ticket.category.value),
                    ServiceTicketModel.description == ticket.description,
                    ServiceTicketModel.first_occurrence == ticket.first_occurrence,
                    ServiceTicketModel.received_error_message
                    == ticket.received_error_message,
                    ServiceTicketModel.error_message_details
                    == ticket.error_message_details,
                    ServiceTicketModel.assignee == ticket.assignee,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create(self, ticket: ServiceTicketCreate) -> ServiceTicketModel:
        """Insert a new ticket and return a managed row."""
        entity = self._model_from_create(ticket)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def update(
        self,
        ticket: ServiceTicketModel,
        payload: ServiceTicketCreate | ServiceTicketUpdate,
    ) -> ServiceTicketModel:
        """Patch an existing row in memory."""
        self._apply_create_payload(ticket, payload)
        await self._session.flush()
        await self._session.refresh(ticket)
        return ticket

    async def delete(self, ticket_id: int) -> bool:
        """Delete a ticket by ID and report whether a row was removed."""
        row = await self._session.get(ServiceTicketModel, ticket_id)
        if row is None:
            return False

        await self._session.delete(row)
        return True

    async def bulk_delete(self, ticket_ids: Sequence[int]) -> int:
        """Delete tickets by ID and return the number of affected rows."""
        if not ticket_ids:
            return 0

        rows = list(
            (
                await self._session.execute(
                    select(ServiceTicketModel).where(
                        ServiceTicketModel.id.in_(ticket_ids)
                    )
                )
            )
            .scalars()
            .all()
        )
        for row in rows:
            await self._session.delete(row)

        return len(rows)

    @staticmethod
    def _model_from_create(ticket: ServiceTicketCreate) -> ServiceTicketModel:
        return ServiceTicketModel(
            urgency=ServiceTicketUrgency(ticket.urgency.value),
            category=ServiceTicketCategory(ticket.category.value),
            description=ticket.description,
            first_occurrence=ticket.first_occurrence,
            received_error_message=ticket.received_error_message,
            error_message_details=ticket.error_message_details,
            assignee=ticket.assignee,
        )

    @staticmethod
    def _apply_create_payload(
        entity: ServiceTicketModel, payload: ServiceTicketCreate | ServiceTicketUpdate
    ) -> None:
        entity.urgency = ServiceTicketUrgency(payload.urgency.value)
        entity.category = ServiceTicketCategory(payload.category.value)
        entity.description = payload.description
        entity.first_occurrence = payload.first_occurrence
        entity.received_error_message = payload.received_error_message
        entity.error_message_details = payload.error_message_details
        entity.assignee = payload.assignee
