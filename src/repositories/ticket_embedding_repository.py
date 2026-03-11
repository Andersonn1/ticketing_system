"""Repository for ticket embeddings and similarity search."""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.llm.embeddings import to_pgvector_str
from src.models import TicketEmbeddingModel
from src.schemas import RetrievedTicketMatchSchema

from .contracts import TicketEmbeddingRepositoryContract


class TicketEmbeddingRepository(TicketEmbeddingRepositoryContract):
    """Async repository for storing and querying ticket embeddings."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_ticket_id(self, ticket_id: int) -> TicketEmbeddingModel | None:
        """Load the embedding row for a ticket."""
        result = await self._session.execute(
            select(TicketEmbeddingModel).where(TicketEmbeddingModel.ticket_id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, *, ticket_id: int, combined_text: str, embedding: list[float]) -> TicketEmbeddingModel:
        """Insert or update the embedding for one ticket."""
        existing = await self.get_by_ticket_id(ticket_id)
        if existing is None:
            entity = TicketEmbeddingModel(
                ticket_id=ticket_id,
                combined_text=combined_text,
                embedding=embedding,
            )
            self._session.add(entity)
            await self._session.flush()
            await self._session.refresh(entity)
            return entity

        existing.combined_text = combined_text
        existing.embedding = embedding
        await self._session.flush()
        await self._session.refresh(existing)
        return existing

    async def search_similar(
        self, embedding: list[float], *, exclude_ticket_id: int, top_k: int
    ) -> list[RetrievedTicketMatchSchema]:
        """Return similar tickets excluding the current ticket."""
        vector = to_pgvector_str(embedding)
        result = await self._session.execute(
            text(
                """
                SELECT
                    te.ticket_id,
                    t.title,
                    te.combined_text,
                    1 - (te.embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM ticket_embedding te
                JOIN ticket t ON t.id = te.ticket_id
                WHERE te.embedding IS NOT NULL
                  AND te.ticket_id <> :exclude_ticket_id
                ORDER BY te.embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
                """
            ),
            {
                "embedding": vector,
                "exclude_ticket_id": exclude_ticket_id,
                "top_k": top_k,
            },
        )
        return [RetrievedTicketMatchSchema.model_validate(dict(row)) for row in result.mappings().all()]
