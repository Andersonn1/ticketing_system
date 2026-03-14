"""Metrics page helper tests."""

from __future__ import annotations

from datetime import datetime
import unittest

from src.models import AIConfidence, ServiceCategory, ServiceDepartment, ServicePriority, ServiceStatus, UserRole
from src.pages.metrics_page import (
    _build_metrics_summary,
    _format_processing_ms,
    _format_similarity,
    _has_ai_triage,
    _has_manual_triage,
    _needs_review,
)
from src.schemas import (
    RetrievedKBMatchSchema,
    RetrievedTicketMatchSchema,
    TicketAITraceSchema,
    TicketResponseSchema,
)


def _ticket(**overrides: object) -> TicketResponseSchema:
    """Build a baseline ticket for metrics tests."""
    payload: dict[str, object] = {
        "id": 7,
        "requestor_name": "Jane Student",
        "requestor_email": "jane@example.edu",
        "user_role": UserRole.STUDENT,
        "title": "Canvas login issue",
        "description": "Login fails after reset",
        "status": ServiceStatus.CLOSED,
        "priority": ServicePriority.MEDIUM,
        "category": ServiceCategory.SOFTWARE_ISSUE,
        "department": ServiceDepartment.HELPDESK,
        "ai_summary": "Summary",
        "ai_recommended_action": "Advise the user to retry after sync completes.",
        "ai_missing_information": "none",
        "ai_reasoning": "The ticket matches a known sync delay issue.",
        "ai_processing_ms": 2200,
        "manual_summary": None,
        "manual_response": None,
        "manual_next_steps": [],
        "ai_confidence": AIConfidence.HIGH,
        "ai_trace": TicketAITraceSchema(
            query_text="Title: Canvas login issue",
            kb_matches=[
                RetrievedKBMatchSchema(
                    id=1,
                    source_name="password_reset_policy",
                    chunk_text="Wait 15 minutes after reset.",
                    metadata={"category": "password_reset"},
                    similarity=0.91,
                )
            ],
            ticket_matches=[
                RetrievedTicketMatchSchema(
                    ticket_id=4,
                    title="Password reset sync delay",
                    combined_text="Title: Password reset sync delay",
                    similarity=0.84,
                )
            ],
        ),
        "created_at": datetime(2026, 3, 13, 12, 0, 0),
        "updated_at": datetime(2026, 3, 13, 12, 5, 0),
    }
    payload.update(overrides)
    return TicketResponseSchema.model_validate(payload)


class MetricsPageHelperTests(unittest.TestCase):
    """Verify metrics aggregation and formatting behavior."""

    def test_triage_presence_helpers_detect_manual_and_ai_records(self) -> None:
        ticket = _ticket()

        self.assertTrue(_has_ai_triage(ticket))
        self.assertFalse(_has_manual_triage(ticket))

        manual_ticket = _ticket(
            manual_summary="Investigated login issue.",
            manual_response="Asked the student to retry.",
            manual_next_steps=["Wait 15 minutes."],
        )

        self.assertTrue(_has_manual_triage(manual_ticket))

    def test_needs_review_flags_low_confidence_or_missing_info(self) -> None:
        self.assertTrue(_needs_review(_ticket(ai_confidence=AIConfidence.LOW)))
        self.assertTrue(_needs_review(_ticket(ai_missing_information="Device type and room number.")))
        self.assertFalse(_needs_review(_ticket()))

    def test_build_metrics_summary_aggregates_counts_and_similarity(self) -> None:
        summary = _build_metrics_summary(
            [
                _ticket(),
                _ticket(
                    id=8,
                    status=ServiceStatus.OPEN,
                    priority=ServicePriority.HIGH,
                    category=ServiceCategory.NETWORK,
                    department=ServiceDepartment.NETWORK_TEAM,
                    ai_confidence=AIConfidence.LOW,
                    ai_missing_information="Access point location.",
                    ai_processing_ms=4200,
                ),
                _ticket(
                    id=9,
                    ai_summary=None,
                    ai_recommended_action=None,
                    ai_missing_information=None,
                    ai_reasoning=None,
                    ai_processing_ms=None,
                    ai_confidence=None,
                    department=None,
                    ai_trace=None,
                    manual_summary="Manual review complete.",
                    manual_response="Resolved by resetting password.",
                    manual_next_steps=["Reset password."],
                    status=ServiceStatus.PENDING,
                    category=ServiceCategory.PASSWORD_RESET,
                ),
            ]
        )

        self.assertEqual(summary.total_tickets, 3)
        self.assertEqual(summary.ai_triaged_tickets, 2)
        self.assertEqual(summary.manual_triaged_tickets, 1)
        self.assertEqual(summary.review_needed_tickets, 1)
        self.assertEqual(summary.missing_information_tickets, 1)
        self.assertEqual(summary.median_ai_processing_ms, 3200)
        self.assertEqual(summary.status_counts[0], ("Closed", 1))
        self.assertIn(("Open", 1), summary.status_counts)
        self.assertIn(("Pending", 1), summary.status_counts)
        self.assertIn(("Helpdesk", 1), summary.department_counts)
        self.assertIn(("Network Team", 1), summary.department_counts)
        self.assertAlmostEqual(summary.average_top_kb_similarity or 0.0, 0.91)
        self.assertAlmostEqual(summary.average_top_ticket_similarity or 0.0, 0.84)
        self.assertEqual(summary.review_rows[0]["id"], 8)

    def test_formatters_handle_missing_values(self) -> None:
        self.assertEqual(_format_processing_ms(None), "N/A")
        self.assertEqual(_format_processing_ms(2500), "2.50s")
        self.assertEqual(_format_similarity(None), "N/A")
        self.assertEqual(_format_similarity(0.91234), "0.912")


if __name__ == "__main__":
    unittest.main()
