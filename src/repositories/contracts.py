"""Repository Contracts"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import KBChunkModel, ServiceStatus, TicketEmbeddingModel, TicketModel
from src.schemas import (
    RetrievedKBMatchSchema,
    RetrievedTicketMatchSchema,
    TicketAITraceSchema,
    TicketCreateSchema,
    TicketUpdateSchema,
    TriageResultSchema,
)


class TicketRepositoryContract(Protocol):
    """Ticket Repository Interface"""

    def __init__(self, session: AsyncSession) -> None: ...

    async def list_all(self) -> list[TicketModel]:
        """Load all tickets in creation order."""
        ...

    async def get_by_id(self, ticket_id: int) -> TicketModel | None:
        """Load a single ticket by primary key."""
        ...

    async def get_by_id_for_update(self, ticket_id: int) -> TicketModel | None:
        """Load and lock a single ticket by primary key for mutation."""
        ...

    async def get_by_ids(self, ticket_ids: Sequence[int]) -> list[TicketModel]:
        """Load multiple tickets preserving database ordering."""
        ...

    async def get_by_business_key(
        self,
        ticket: TicketCreateSchema,
    ) -> TicketModel | None:
        """Load a ticket by stable business fields."""
        ...

    async def create(self, ticket: TicketCreateSchema) -> TicketModel:
        """Insert a new ticket and return a managed row."""
        ...

    async def update(
        self,
        ticket: TicketModel,
        payload: TicketCreateSchema | TicketUpdateSchema,
    ) -> TicketModel:
        """Patch an existing row in memory."""
        ...

    async def claim_for_triage(self, ticket_id: int) -> TicketModel | None:
        """Atomically move an open ticket into pending triage state."""
        ...

    async def set_status(self, ticket: TicketModel, status: ServiceStatus) -> TicketModel:
        """Update only the ticket status."""
        ...

    async def apply_triage(
        self,
        ticket: TicketModel,
        triage: TriageResultSchema,
        trace: TicketAITraceSchema,
    ) -> TicketModel:
        """Persist AI triage fields onto a ticket."""
        ...

    async def delete(self, ticket_id: int) -> bool:
        """Delete a ticket by ID and report whether a row was removed."""
        ...

    async def bulk_delete(self, ticket_ids: Sequence[int]) -> int:
        """Delete tickets by ID and return the number of affected rows."""
        ...

    @staticmethod
    def _model_from_create(ticket: TicketCreateSchema) -> TicketModel:
        """Map Ticker Create Data to Model"""
        ...

    @staticmethod
    def _apply_create_payload(entity: TicketModel, payload: TicketCreateSchema | TicketUpdateSchema) -> None:
        """Handle Model Data Mapping"""
        ...


class TicketEmbeddingRepositoryContract(Protocol):
    """Ticket Embeddings Repository Interface"""

    def __init__(self, session: AsyncSession) -> None: ...

    async def get_by_ticket_id(self, ticket_id: int) -> TicketEmbeddingModel | None:
        """Load the embedding row for a ticket."""
        ...

    async def upsert(self, *, ticket_id: int, combined_text: str, embedding: list[float]) -> TicketEmbeddingModel:
        """Insert or update the embedding for one ticket."""
        ...

    async def search_similar(
        self, embedding: list[float], *, exclude_ticket_id: int, top_k: int
    ) -> list[RetrievedTicketMatchSchema]:
        """Return similar tickets excluding the current ticket."""
        ...


class KBChunkRepositoryContract(Protocol):
    """KBChunk Repository Interface"""

    def __init__(self, session: AsyncSession) -> None: ...

    async def get_by_source_name(self, source_name: str) -> KBChunkModel | None:
        """Load a KB chunk by its stable source name."""
        ...

    async def upsert(
        self,
        *,
        source_name: str,
        chunk_text: str,
        metadata: dict[str, Any],
        embedding: list[float],
    ) -> KBChunkModel:
        """Insert or update one KB chunk."""
        ...

    async def search_similar(self, embedding: list[float], *, top_k: int) -> list[RetrievedKBMatchSchema]:
        """Return the most similar KB chunks for a query embedding."""
        ...
