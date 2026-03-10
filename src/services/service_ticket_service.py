"""Service-layer orchestration for service tickets."""

from __future__ import annotations

from dataclasses import dataclass

from src.db.session import get_session
from src.models.service_ticket_model import (
    ServiceCategory as ServiceTicketCategory,
    ServiceTicketModel,
    ServiceUrgency as ServiceTicketUrgency,
)
from src.repositories.service_ticket_repository import ServiceTicketRepository
from src.schemas.service_ticket import (
    ServiceTicket,
    ServiceTicketCreate,
    ServiceTicketUpdate,
)


@dataclass(slots=True)
class SeedSummary:
    """Summary of seed/upsert counts."""

    created: int
    updated: int
    skipped: int


class ServiceTicketService:
    """High-level ticket service using repository operations."""

    async def list_tickets(self) -> list[ServiceTicket]:
        """Return all tickets from the database."""
        async with get_session() as session:
            repository = ServiceTicketRepository(session)
            rows = await repository.list_all()
            return [self._to_schema(row) for row in rows]

    async def get_ticket(self, ticket_id: int) -> ServiceTicket | None:
        """Return a single ticket by PK."""
        async with get_session() as session:
            repository = ServiceTicketRepository(session)
            row = await repository.get_by_id(ticket_id)
            return self._to_schema(row) if row is not None else None

    async def create_ticket(self, payload: ServiceTicketCreate) -> ServiceTicket:
        """Create one ticket and return it."""
        async with get_session() as session:
            repository = ServiceTicketRepository(session)
            row = await repository.create(payload)
            await session.commit()
            await session.refresh(row)
            return self._to_schema(row)

    async def update_ticket(
        self, ticket_id: int, payload: ServiceTicketUpdate
    ) -> ServiceTicket | None:
        """Update a ticket by ID."""
        async with get_session() as session:
            repository = ServiceTicketRepository(session)
            row = await repository.get_by_id(ticket_id)
            if row is None:
                return None
            row = await repository.update(row, payload)
            await session.commit()
            return self._to_schema(row)

    async def delete_ticket(self, ticket_id: int) -> bool:
        """Delete one ticket by ID."""
        async with get_session() as session:
            repository = ServiceTicketRepository(session)
            result = await repository.delete(ticket_id)
            if result:
                await session.commit()
            return result

    async def seed_tickets(
        self, payloads: list[ServiceTicketCreate]
    ) -> SeedSummary:
        """Seed/reconcile rows from JSON payloads by business key."""
        created = 0
        updated = 0
        skipped = 0

        async with get_session() as session:
            repository = ServiceTicketRepository(session)
            for payload in payloads:
                existing = await repository.get_by_business_key(payload)
                if existing is None:
                    await repository.create(payload)
                    created += 1
                    continue

                if self._requires_update(existing, payload):
                    await repository.update(existing, payload)
                    updated += 1
                else:
                    skipped += 1

            await session.commit()

        return SeedSummary(created=created, updated=updated, skipped=skipped)

    @staticmethod
    def _requires_update(entity: ServiceTicketModel, payload: ServiceTicketCreate) -> bool:
        return (
            entity.urgency != ServiceTicketUrgency(payload.urgency.value)
            or entity.category != ServiceTicketCategory(payload.category.value)
            or entity.description != payload.description
            or entity.first_occurrence != payload.first_occurrence
            or entity.received_error_message != payload.received_error_message
            or entity.error_message_details != payload.error_message_details
            or entity.assignee != payload.assignee
        )

    @staticmethod
    def _to_schema(row: ServiceTicketModel) -> ServiceTicket:
        ticket_payload = {
            "id": row.id,
            "urgency": row.urgency.value if isinstance(row.urgency, ServiceTicketUrgency) else row.urgency,
            "category": row.category.value if isinstance(row.category, ServiceTicketCategory) else row.category,
            "description": row.description,
            "first_occurrence": row.first_occurrence,
            "received_error_message": row.received_error_message,
            "error_message_details": row.error_message_details,
            "assignee": row.assignee,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        return ServiceTicket.model_validate(ticket_payload)
