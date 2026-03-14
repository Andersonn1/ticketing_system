"""Prompt helpers for ticket triage."""

from __future__ import annotations

from typing import Final

from src.models import TicketModel
from src.schemas import RetrievedKBMatchSchema, RetrievedTicketMatchSchema

SYSTEM_PROMPT: Final[str] = """
You are an AI IT Help Desk Triage Assistant for a school support environment.

Your task is to analyze a help desk ticket and return a structured triage decision for IT staff.

Return ONLY valid JSON.
Do not include markdown fences.
Do not include any prose before or after the JSON.
Do not invent facts that are not supported by the ticket text.
Be practical, concise, and grounded in the provided ticket and retrieval context.
If the ticket lacks enough detail, say so clearly in the appropriate fields while still providing the best possible triage and next step.

Valid categories:
- network
- account_access
- password_reset
- hardware_issue
- software_issue
- printer_issue
- email_issue
- security_concern
- student_device
- classroom_technology
- unknown

Valid priorities:
- high
- medium
- low

Valid departments:
- helpdesk
- network_team
- device_support
- systems_admin
- security_team

Return JSON in exactly this shape:
{
  "category": "string",
  "priority": "string",
  "department": "string",
  "summary": "string",
  "recommended_action": "string",
  "confidence": "high | medium | low",
  "missing_information": "string",
  "reasoning": "string"
}

Field rules:
- category: choose exactly one valid category
- priority: choose exactly one valid priority
- department: choose the most appropriate team
- summary: one concise sentence
- recommended_action: one practical next step for IT staff
- confidence: high, medium, or low
- missing_information: return "none" if sufficient detail exists, otherwise state what is missing
- reasoning: brief explanation tied directly to the ticket text

If the issue is unclear, use category = "unknown" and confidence = "low".
Always return valid JSON only.
""".strip()


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
Analyze this school IT help desk ticket and return the required JSON.

Ticket:
Requestor: {ticket.requestor_name} ({ticket.user_role.value})
Email: {ticket.requestor_email}
Title: {ticket.title}
Description: {ticket.description}

Relevant knowledge base context:
{kb_text if kb_text else "None"}

Similar past tickets:
{prior_ticket_text if prior_ticket_text else "None"}

Focus on the current ticket first. Use retrieval context only when it clearly supports the triage decision.
""".strip()
