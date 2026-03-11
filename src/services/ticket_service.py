"""Service layer orchestration for tickets and AI triage."""

from __future__ import annotations

import asyncio
from time import perf_counter
from typing import Any

from loguru import logger

from src.llm.triage import (
    KB_TOP_K,
    TICKET_TOP_K,
    build_ai_trace,
    build_prompt,
    build_query_text,
    build_ticket_embedding_text,
)
from src.models import ServiceStatus, TicketModel
from src.repositories import (
    KBChunkRepository,
    TicketEmbeddingRepository,
    TicketRepository,
)
from src.schemas import (
    ManualTriageSchema,
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
        logger.debug("Listing tickets from the database.")
        async with self._session_provider() as session:
            repository = TicketRepository(session)
            rows = await repository.list_all()
            response = [self._to_schema(row) for row in rows]
            logger.info("Loaded {} tickets from the database.", len(response))
            return response

    async def get_ticket(self, ticket_id: int) -> TicketResponseSchema | None:
        """Return a single ticket by PK."""
        logger.debug("Loading ticket {} from the database.", ticket_id)
        async with self._session_provider() as session:
            repository = TicketRepository(session)
            row = await repository.get_by_id(ticket_id)
            if row is None:
                logger.warning("Ticket {} was not found.", ticket_id)
            else:
                logger.debug("Loaded ticket {}.", ticket_id)
            return self._to_schema(row) if row is not None else None

    async def create_ticket(self, payload: TicketCreateSchema) -> TicketResponseSchema:
        """Create one ticket and return it."""
        logger.info("Creating ticket for {} with title '{}'.", payload.requestor_email, payload.title)
        async with self._session_provider() as session:
            repository = TicketRepository(session)
            row = await repository.create(payload)
            await session.commit()
            await session.refresh(row)
            logger.info("Created ticket {}.", row.id)
            return self._to_schema(row)

    async def update_ticket(self, ticket_id: int, payload: TicketUpdateSchema) -> TicketResponseSchema | None:
        """Update a ticket by ID."""
        logger.info("Updating ticket {}.", ticket_id)
        async with self._session_provider() as session:
            repository = TicketRepository(session)
            row = await repository.get_by_id_for_update(ticket_id)
            if row is None:
                logger.warning("Unable to update ticket {} because it was not found.", ticket_id)
                return None
            self._validate_manual_status_transition(ticket_id, row.status, payload.status)
            row = await repository.update(row, payload)
            await session.commit()
            logger.info("Updated ticket {}.", ticket_id)
            return self._to_schema(row)

    async def manual_triage_ticket(
        self,
        ticket_id: int,
        payload: ManualTriageSchema,
    ) -> TicketResponseSchema | None:
        """Persist manual triage content and worker-selected triage fields."""
        logger.info("Saving manual triage for ticket {}.", ticket_id)
        async with self._session_provider() as session:
            repository = TicketRepository(session)
            row = await repository.get_by_id_for_update(ticket_id)
            if row is None:
                logger.warning("Unable to manually triage ticket {} because it was not found.", ticket_id)
                return None
            self._validate_manual_triage_transition(ticket_id, row.status, payload.status)
            row = await repository.apply_manual_triage(row, payload)
            await session.commit()
            logger.info("Saved manual triage for ticket {}.", ticket_id)
            return self._to_schema(row)

    async def delete_ticket(self, ticket_id: int) -> bool:
        """Delete one ticket by ID."""
        logger.info("Deleting ticket {}.", ticket_id)
        async with self._session_provider() as session:
            repository = TicketRepository(session)
            result = await repository.delete(ticket_id)
            if result:
                await session.commit()
                logger.info("Deleted ticket {}.", ticket_id)
            else:
                logger.warning("Unable to delete ticket {} because it was not found.", ticket_id)
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
        started_at = perf_counter()
        logger.info("Starting AI triage for ticket {}.", ticket_id)
        async with self._session_provider() as session:
            ticket_repository = TicketRepository(session)
            kb_repository = KBChunkRepository(session)
            embedding_repository = TicketEmbeddingRepository(session)
            ticket = await ticket_repository.claim_for_triage(ticket_id)
            if ticket is None:
                current_ticket = await ticket_repository.get_by_id(ticket_id)
                if current_ticket is None:
                    logger.warning("AI triage failed because ticket {} was not found.", ticket_id)
                    raise ValueError(f"Ticket {ticket_id} was not found")
                if current_ticket.status == ServiceStatus.PENDING:
                    logger.warning("Ticket {} is already being triaged.", ticket_id)
                    raise ValueError(f"Ticket {ticket_id} is already being triaged")
                logger.warning(
                    "Ticket {} cannot be triaged because it is currently {}.",
                    ticket_id,
                    current_ticket.status,
                )
                raise ValueError(
                    f"Ticket {ticket_id} cannot be triaged because it is {current_ticket.status.value.title()}"
                )

            await session.commit()
            await session.refresh(ticket)
            logger.info("Ticket {} claimed for triage and moved to Pending.", ticket_id)
            try:
                query_text = build_query_text(ticket)
                query_embedding = await self._ollama_client.embed_text(query_text)
                logger.debug("Generated query embedding for ticket {}.", ticket_id)
                kb_matches = await kb_repository.search_similar(query_embedding, top_k=KB_TOP_K)
                ticket_matches = await embedding_repository.search_similar(
                    query_embedding,
                    exclude_ticket_id=ticket_id,
                    top_k=TICKET_TOP_K,
                )
                logger.info(
                    "Retrieved triage context for ticket {}: {} KB matches and {} similar tickets.",
                    ticket_id,
                    len(kb_matches),
                    len(ticket_matches),
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
                await ticket_repository.set_status(ticket, ServiceStatus.CLOSED)
                await session.commit()
                await session.refresh(ticket)
                logger.info(
                    "Completed AI triage for ticket {} in {:.2f}s.",
                    ticket_id,
                    perf_counter() - started_at,
                )
                return self._to_schema(ticket)
            except Exception:
                logger.exception("AI triage failed for ticket {}.", ticket_id)
                await session.rollback()
                try:
                    current_ticket = await ticket_repository.get_by_id(ticket_id)
                    if current_ticket is not None and current_ticket.status == ServiceStatus.PENDING:
                        await ticket_repository.set_status(current_ticket, ServiceStatus.OPEN)
                        await session.commit()
                        logger.info("Reset ticket {} back to Open after triage failure.", ticket_id)
                except Exception:
                    logger.exception("Unable to reset ticket {} after triage failure.", ticket_id)
                raise

    async def triage_tickets(self, ticket_ids: list[int]) -> TriageBatchResult:
        """Run AI triage for a list of tickets concurrently."""
        if not ticket_ids:
            logger.warning("Skipping AI triage because no ticket IDs were provided.")
            return TriageBatchResult(completed=[], failed={})

        started_at = perf_counter()
        logger.info("Starting AI triage batch for {} tickets: {}", len(ticket_ids), ticket_ids)
        results = await asyncio.gather(
            *(self.triage_ticket(ticket_id) for ticket_id in ticket_ids),
            return_exceptions=True,
        )

        completed: list[int] = []
        failed: dict[int, str] = {}
        for ticket_id, result in zip(ticket_ids, results, strict=True):
            if isinstance(result, Exception):
                failed[ticket_id] = str(result)
                logger.warning("AI triage failed for ticket {}: {}", ticket_id, result)
                continue
            completed.append(ticket_id)

        logger.info(
            "AI triage batch finished in {:.2f}s. Completed: {}. Failed: {}.",
            perf_counter() - started_at,
            completed,
            failed,
        )
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
    def _validate_manual_status_transition(
        ticket_id: int,
        current_status: ServiceStatus,
        requested_status: ServiceStatus | None,
    ) -> None:
        """Reject manual transitions that conflict with triage ownership."""
        if requested_status is None or requested_status == current_status:
            return

        allowed_transitions = {
            (ServiceStatus.OPEN, ServiceStatus.PENDING),
            (ServiceStatus.OPEN, ServiceStatus.CLOSED),
        }
        if (current_status, requested_status) in allowed_transitions:
            return

        if current_status == ServiceStatus.PENDING:
            raise ValueError(f"Ticket {ticket_id} is currently being triaged and cannot be updated.")

        raise ValueError(
            f"Ticket {ticket_id} cannot move from {current_status.value.title()} to {requested_status.value.title()}."
        )

    @staticmethod
    def _validate_manual_triage_transition(
        ticket_id: int,
        current_status: ServiceStatus,
        requested_status: ServiceStatus,
    ) -> None:
        """Allow manual triage while a ticket is open or pending, but never after closure."""
        allowed_transitions = {
            (ServiceStatus.OPEN, ServiceStatus.PENDING),
            (ServiceStatus.OPEN, ServiceStatus.CLOSED),
            (ServiceStatus.PENDING, ServiceStatus.PENDING),
            (ServiceStatus.PENDING, ServiceStatus.CLOSED),
        }
        if (current_status, requested_status) in allowed_transitions:
            return
        if current_status == ServiceStatus.CLOSED:
            raise ValueError(f"Ticket {ticket_id} has already been closed and cannot be manually triaged.")
        raise ValueError(
            f"Ticket {ticket_id} cannot move from {current_status.value.title()} to {requested_status.value.title()}."
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
            "manual_summary": row.manual_summary,
            "manual_response": row.manual_response,
            "manual_next_steps": row.manual_next_steps or [],
            "ai_confidence": row.ai_confidence,
            "ai_trace": row.ai_trace,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        return TicketResponseSchema.model_validate(ticket_payload)
