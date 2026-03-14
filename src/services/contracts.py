"""Service Contracts"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import TicketModel
from src.schemas import (
    ManualTriageSchema,
    TicketCreateSchema,
    TicketResponseSchema,
    TicketUpdateSchema,
    TriageResultSchema,
)

from .models import SeedSummary, TriageBatchResult

SessionProvider = Callable[[], AbstractAsyncContextManager[AsyncSession]]


class SupportsTriageLLMContract(Protocol):
    """Supports Triage LLM Interface."""

    async def embed_text(self, text: str) -> list[float]: ...

    async def chat_json(self, prompt: str) -> TriageResultSchema: ...


class TicketServiceContract(Protocol):
    """Ticket Service Interface"""

    def __init__(
        self,
        *,
        session_provider: SessionProvider,
        llm_client: SupportsTriageLLMContract,
    ) -> None:
        """Initialize the service with explicit runtime dependencies."""
        ...

    async def list_tickets(self) -> list[TicketResponseSchema]:
        """Return all tickets from the database."""
        ...

    async def get_ticket(self, ticket_id: int) -> TicketResponseSchema | None:
        """Return a single ticket by PK."""
        ...

    async def create_ticket(self, payload: TicketCreateSchema) -> TicketResponseSchema:
        """Create one ticket and return it."""
        ...

    async def update_ticket(self, ticket_id: int, payload: TicketUpdateSchema) -> TicketResponseSchema | None:
        """Update a ticket by ID."""
        ...

    async def manual_triage_ticket(
        self,
        ticket_id: int,
        payload: ManualTriageSchema,
    ) -> TicketResponseSchema | None:
        """Persist manual triage content and worker-selected triage fields."""
        ...

    async def delete_ticket(self, ticket_id: int) -> bool:
        """Delete one ticket by ID."""
        ...

    async def seed_tickets(self, payloads: list[TicketCreateSchema]) -> SeedSummary:
        """Seed/reconcile rows from JSON payloads by business key."""
        ...

    async def seed_kb_docs(self, docs: list[dict[str, Any]]) -> int:
        """Upsert KB docs and their embeddings."""
        ...

    async def refresh_ticket_embeddings(self) -> int:
        """Regenerate embeddings for all tickets."""
        ...

    async def triage_ticket(self, ticket_id: int) -> TicketResponseSchema:
        """Run AI triage for one ticket and persist the results."""
        ...

    async def triage_tickets(self, ticket_ids: list[int]) -> TriageBatchResult:
        """Run AI triage for a list of tickets concurrently."""
        ...

    @staticmethod
    def _requires_update(entity: TicketModel, payload: TicketCreateSchema) -> bool:
        """Check if existing data needs to be updated"""
        ...

    @staticmethod
    def _to_schema(row: TicketModel) -> TicketResponseSchema:
        """Convert Model to Schema Response"""
        ...
