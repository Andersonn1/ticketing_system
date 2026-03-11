"""Service layer orchestration for tickets and AI triage."""

from __future__ import annotations

import asyncio
from typing import Any

from src.llm.triage import (
    KB_TOP_K,
    TICKET_TOP_K,
    build_ai_trace,
    build_prompt,
    build_query_text,
    build_ticket_embedding_text,
)
from src.models import TicketModel
from src.repositories import (
    KBChunkRepository,
    TicketEmbeddingRepository,
    TicketRepository,
)
from src.schemas import (
    TicketCreateSchema,
    TicketResponseSchema,
    TicketUpdateSchema,
)

from .contracts import SessionProvider, SupportsTriageLLMContract, TicketServiceContract
from .models import SeedSummary, TriageBatchResult


class TicketService(TicketServiceContract):
    """Ticket Service."""

    __slots__ = ("_ollama_client", "_session_provider")

    def __init__(
        self,
        *,
        session_provider: SessionProvider,
        ollama_client: SupportsTriageLLMContract,
    ) -> None:
        self._session_provider = session_provider
        self._ollama_client = ollama_client

    async def list_tickets(self) -> list[TicketResponseSchema]:
        """Return all tickets from the database."""
        async with self._session_provider() as session:
            repository = TicketRepository(session)
            rows = await repository.list_all()
            return [self._to_schema(row) for row in rows]

    async def get_ticket(self, ticket_id: int) -> TicketResponseSchema | None:
        """Return a single ticket by PK."""
        async with self._session_provider() as session:
            repository = TicketRepository(session)
            row = await repository.get_by_id(ticket_id)
            return self._to_schema(row) if row is not None else None

    async def create_ticket(self, payload: TicketCreateSchema) -> TicketResponseSchema:
        """Create one ticket and return it."""
        async with self._session_provider() as session:
            repository = TicketRepository(session)
            row = await repository.create(payload)
            await session.commit()
            await session.refresh(row)
            return self._to_schema(row)

    async def update_ticket(self, ticket_id: int, payload: TicketUpdateSchema) -> TicketResponseSchema | None:
        """Update a ticket by ID."""
        async with self._session_provider() as session:
            repository = TicketRepository(session)
            row = await repository.get_by_id(ticket_id)
            if row is None:
                return None
            row = await repository.update(row, payload)
            await session.commit()
            return self._to_schema(row)

    async def delete_ticket(self, ticket_id: int) -> bool:
        """Delete one ticket by ID."""
        async with self._session_provider() as session:
            repository = TicketRepository(session)
            result = await repository.delete(ticket_id)
            if result:
                await session.commit()
            return result

    async def seed_tickets(self, payloads: list[TicketCreateSchema]) -> SeedSummary:
        """Seed/reconcile rows from JSON payloads by business key."""
        created = 0
        updated = 0
        skipped = 0

        async with self._session_provider() as session:
            repository = TicketRepository(session)
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

    async def seed_kb_docs(self, docs: list[dict[str, Any]]) -> int:
        """Upsert KB docs and their embeddings."""
        upserted = 0
        async with self._session_provider() as session:
            repository = KBChunkRepository(session)
            for doc in docs:
                embedding = await self._ollama_client.embed_text(str(doc["chunk_text"]))
                await repository.upsert(
                    source_name=str(doc["source_name"]),
                    chunk_text=str(doc["chunk_text"]),
                    metadata=dict(doc.get("metadata", {})),
                    embedding=embedding,
                )
                upserted += 1
            await session.commit()

        return upserted

    async def triage_ticket(self, ticket_id: int) -> TicketResponseSchema:
        """Run AI triage for one ticket and persist the results."""
        async with self._session_provider() as session:
            ticket_repository = TicketRepository(session)
            kb_repository = KBChunkRepository(session)
            embedding_repository = TicketEmbeddingRepository(session)

            ticket = await ticket_repository.get_by_id(ticket_id)
            if ticket is None:
                raise ValueError(f"Ticket {ticket_id} was not found")

            query_text = build_query_text(ticket)
            query_embedding = await self._ollama_client.embed_text(query_text)
            kb_matches = await kb_repository.search_similar(query_embedding, top_k=KB_TOP_K)
            ticket_matches = await embedding_repository.search_similar(
                query_embedding,
                exclude_ticket_id=ticket_id,
                top_k=TICKET_TOP_K,
            )
            triage_result = await self._ollama_client.chat_json(build_prompt(ticket, kb_matches, ticket_matches))
            ai_trace = build_ai_trace(
                query_text=query_text,
                kb_matches=kb_matches,
                ticket_matches=ticket_matches,
            )

            await ticket_repository.apply_triage(ticket, triage_result, ai_trace)
            await embedding_repository.upsert(
                ticket_id=ticket.id,
                combined_text=build_ticket_embedding_text(ticket),
                embedding=query_embedding,
            )
            await session.commit()
            await session.refresh(ticket)
            return self._to_schema(ticket)

    async def triage_tickets(self, ticket_ids: list[int]) -> TriageBatchResult:
        """Run AI triage for a list of tickets concurrently."""
        if not ticket_ids:
            return TriageBatchResult(completed=[], failed={})

        results = await asyncio.gather(
            *(self.triage_ticket(ticket_id) for ticket_id in ticket_ids),
            return_exceptions=True,
        )

        completed: list[int] = []
        failed: dict[int, str] = {}
        for ticket_id, result in zip(ticket_ids, results, strict=True):
            if isinstance(result, Exception):
                failed[ticket_id] = str(result)
                continue
            completed.append(ticket_id)

        return TriageBatchResult(completed=completed, failed=failed)

    @staticmethod
    def _requires_update(entity: TicketModel, payload: TicketCreateSchema) -> bool:
        return (
            entity.requestor_name != payload.requestor_name
            or entity.requestor_email != payload.requestor_email
            or entity.user_role != payload.user_role
            or entity.title != payload.title
            or entity.description != payload.description
        )

    @staticmethod
    def _to_schema(row: TicketModel) -> TicketResponseSchema:
        ticket_payload = {
            "id": row.id,
            "requestor_name": row.requestor_name,
            "requestor_email": row.requestor_email,
            "user_role": row.user_role,
            "title": row.title,
            "description": row.description,
            "status": row.status,
            "priority": row.priority,
            "category": row.category,
            "ai_summary": row.ai_summary,
            "ai_response": row.ai_response,
            "ai_next_steps": row.ai_next_steps or [],
            "ai_confidence": row.ai_confidence,
            "ai_trace": row.ai_trace,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        return TicketResponseSchema.model_validate(ticket_payload)
