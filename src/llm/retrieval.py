"""Pure helpers for retrieval and trace construction."""

from __future__ import annotations

from typing import Final

from src.models import TicketModel
from src.schemas import (
    RetrievedKBMatchSchema,
    RetrievedTicketMatchSchema,
    TicketAITraceSchema,
)

KB_TOP_K: Final[int] = 3
TICKET_TOP_K: Final[int] = 2


def build_query_text(ticket: TicketModel) -> str:
    """Build the text used for ticket embeddings and retrieval."""
    return "\n\n".join(
        [
            f"Title: {ticket.title}",
            f"Description: {ticket.description}",
            f"Requestor Role: {ticket.user_role.value}",
        ]
    )


def build_ai_trace(
    *,
    query_text: str,
    kb_matches: list[RetrievedKBMatchSchema],
    ticket_matches: list[RetrievedTicketMatchSchema],
) -> TicketAITraceSchema:
    """Create the persisted retrieval trace for a triage run."""
    return TicketAITraceSchema(
        query_text=query_text,
        kb_matches=kb_matches,
        ticket_matches=ticket_matches,
    )


def build_ticket_embedding_text(ticket: TicketModel) -> str:
    """Build the text stored with a ticket embedding."""
    return "\n".join([f"Title: {ticket.title}", f"Description: {ticket.description}"])
