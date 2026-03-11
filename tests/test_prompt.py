"""Prompt and trace helper tests."""

from __future__ import annotations

import unittest

from src.llm.prompt import build_prompt
from src.llm.retrieval import build_ai_trace, build_query_text
from src.models import (
    ServiceCategory,
    ServicePriority,
    ServiceStatus,
    TicketModel,
    UserRole,
)
from src.schemas import RetrievedKBMatchSchema, RetrievedTicketMatchSchema


class PromptTests(unittest.TestCase):
    """Verify prompt and trace helper behavior."""

    def test_build_prompt_includes_ticket_and_context(self) -> None:
        ticket = TicketModel(
            id=1,
            requestor_name="Jane Student",
            requestor_email="jane@example.edu",
            user_role=UserRole.STUDENT,
            title="Canvas login issue",
            description="Login fails after reset",
            status=ServiceStatus.OPEN,
            priority=ServicePriority.LOW,
            category=ServiceCategory.OTHER,
            ai_summary=None,
            ai_response=None,
            ai_next_steps=[],
            ai_confidence=None,
            ai_trace=None,
        )
        prompt = build_prompt(
            ticket,
            [
                RetrievedKBMatchSchema(
                    id=10,
                    source_name="password_reset_policy",
                    chunk_text="Wait 15 minutes after reset.",
                    metadata={"category": "authentication"},
                    similarity=0.99,
                )
            ],
            [
                RetrievedTicketMatchSchema(
                    ticket_id=5,
                    title="Password reset sync delay",
                    combined_text="Title: Password reset sync delay",
                    similarity=0.92,
                )
            ],
        )

        self.assertIn("Canvas login issue", prompt)
        self.assertIn("password_reset_policy", prompt)
        self.assertIn("Password reset sync delay", prompt)

    def test_build_ai_trace_preserves_matches(self) -> None:
        trace = build_ai_trace(
            query_text="Title: Canvas login issue",
            kb_matches=[
                RetrievedKBMatchSchema(
                    id=1,
                    source_name="policy",
                    chunk_text="chunk",
                    metadata={},
                    similarity=0.88,
                )
            ],
            ticket_matches=[],
        )

        self.assertEqual(trace.query_text, "Title: Canvas login issue")
        self.assertEqual(trace.kb_matches[0].source_name, "policy")

    def test_build_query_text_uses_role_title_and_description(self) -> None:
        ticket = TicketModel(
            id=1,
            requestor_name="Jane Student",
            requestor_email="jane@example.edu",
            user_role=UserRole.STUDENT,
            title="Canvas login issue",
            description="Login fails after reset",
            status=ServiceStatus.OPEN,
            priority=ServicePriority.LOW,
            category=ServiceCategory.OTHER,
            ai_summary=None,
            ai_response=None,
            ai_next_steps=[],
            ai_confidence=None,
            ai_trace=None,
        )

        query_text = build_query_text(ticket)
        self.assertIn("Canvas login issue", query_text)
        self.assertIn("student", query_text)


if __name__ == "__main__":
    unittest.main()
