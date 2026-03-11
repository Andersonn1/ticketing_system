"""Prompt helpers for ticket triage."""

from __future__ import annotations

from src.models import TicketModel
from src.schemas import RetrievedKBMatchSchema, RetrievedTicketMatchSchema

SYSTEM_PROMPT = """
You are a school IT help desk assistant.

Return ONLY valid JSON.
Do not include markdown fences or any prose before/after the JSON.
Be practical, concise, and grounded in the provided context.
If the context is weak, say so explicitly in the response while still providing next steps.
"""


def build_prompt(
    ticket: TicketModel,
    kb_matches: list[RetrievedKBMatchSchema],
    ticket_matches: list[RetrievedTicketMatchSchema],
) -> str:
    """Build the user prompt for AI triage."""
    kb_text = "\n\n".join(
        [
            (
                f"[KB {index}] Source: {match.source_name}\n"
                f"Similarity: {match.similarity:.3f}\n"
                f"Content: {match.chunk_text}"
            )
            for index, match in enumerate(kb_matches, start=1)
        ]
    )
    prior_ticket_text = "\n\n".join(
        [
            (
                f"[Similar Ticket {index}] Ticket ID: {match.ticket_id}\n"
                f"Title: {match.title}\n"
                f"Similarity: {match.similarity:.3f}\n"
                f"Content: {match.combined_text}"
            )
            for index, match in enumerate(ticket_matches, start=1)
        ]
    )

    return f"""
            Ticket:
            Requestor: {ticket.requestor_name} ({ticket.user_role.value})
            Email: {ticket.requestor_email}
            Title: {ticket.title}
            Description: {ticket.description}

            Relevant knowledge base context:
            {kb_text if kb_text else "None"}

            Similar past tickets:
            {prior_ticket_text if prior_ticket_text else "None"}

            Return JSON with this exact shape:
            {{
            "category": "hardware|software|network|security|other",
            "priority": "low|medium|high",
            "summary": "string",
            "response": "string",
            "next_steps": ["string"],
            "confidence": "low|medium|high"
            }}
        """.strip()
