"""Manual triage modal helper tests."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from src.components.ticket_table.manual_triage_modal import (
    _build_manual_triage_payload,
    _manual_triage_enabled,
    _manual_triage_form_defaults,
    _manual_triage_status_options,
    _manual_triage_success_message,
)
from src.models import ServiceCategory, ServicePriority, ServiceStatus, UserRole
from src.schemas import TicketResponseSchema


def _row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "id": 7,
        "requestor_name": "Jane Student",
        "requestor_email": "jane@example.edu",
        "user_role": "Student",
        "title": "Canvas login issue",
        "description": "Login fails after reset",
        "status": "Open",
        "priority": "Low",
        "category": "Unknown",
        "manual_summary": None,
        "manual_response": None,
        "manual_next_steps": [],
        "ai_summary": None,
        "ai_recommended_action": None,
        "ai_missing_information": None,
        "ai_reasoning": None,
        "ai_processing_ms": None,
        "ai_confidence": None,
        "ai_trace": None,
        "created_at": None,
        "updated_at": None,
    }
    row.update(overrides)
    return row


class ManualTriageModalHelperTests(unittest.TestCase):
    """Verify manual triage modal helper behavior."""

    def test_manual_triage_enabled_for_open_and_pending_only(self) -> None:
        self.assertTrue(_manual_triage_enabled(_row(status="Open")))
        self.assertTrue(_manual_triage_enabled(_row(status="Pending")))
        self.assertFalse(_manual_triage_enabled(_row(status="Closed")))

    def test_manual_triage_status_options_for_open_row(self) -> None:
        options = _manual_triage_status_options(_row(status="Open"))

        self.assertEqual(options, {"pending": "Pending", "closed": "Closed"})

    def test_manual_triage_form_defaults_prefill_existing_values(self) -> None:
        defaults = _manual_triage_form_defaults(
            _row(
                status="Pending",
                priority="High",
                category="Security Concern",
                manual_summary="Existing summary",
                manual_response="Existing response",
                manual_next_steps=["Step one", "Step two"],
            )
        )

        self.assertEqual(defaults["summary"], "Existing summary")
        self.assertEqual(defaults["response"], "Existing response")
        self.assertEqual(defaults["next_steps"], "Step one\nStep two")
        self.assertEqual(defaults["priority"], "high")
        self.assertEqual(defaults["category"], "security_concern")
        self.assertEqual(defaults["status"], "pending")

    def test_build_manual_triage_payload_maps_modal_values(self) -> None:
        payload = _build_manual_triage_payload(
            _row(status="Open"),
            {
                "summary": "  Existing login sync issue.  ",
                "response": "  We advised the student to retry after sync completes.  ",
                "next_steps": " Wait 15 minutes. \n Retry Canvas after clearing cache. ",
                "priority": "medium",
                "category": "software_issue",
                "status": "closed",
            },
        )

        self.assertEqual(payload.summary, "Existing login sync issue.")
        self.assertEqual(payload.response, "We advised the student to retry after sync completes.")
        self.assertEqual(payload.next_steps, ["Wait 15 minutes.", "Retry Canvas after clearing cache."])
        self.assertEqual(payload.priority, ServicePriority.MEDIUM)
        self.assertEqual(payload.category, ServiceCategory.SOFTWARE_ISSUE)
        self.assertEqual(payload.status, ServiceStatus.CLOSED)

    def test_build_manual_triage_payload_rejects_blank_status_with_validation_error(self) -> None:
        with self.assertRaises(ValidationError) as context:
            _build_manual_triage_payload(
                _row(status="Open"),
                {
                    "summary": "Existing login sync issue.",
                    "response": "We advised the student to retry after sync completes.",
                    "next_steps": "Wait 15 minutes.",
                    "priority": "medium",
                    "category": "software_issue",
                    "status": "",
                },
            )

        self.assertEqual(context.exception.errors()[0]["loc"], ("status",))

    def test_manual_triage_success_message_mentions_status(self) -> None:
        ticket = TicketResponseSchema(
            id=7,
            requestor_name="Jane Student",
            requestor_email="jane@example.edu",
            user_role=UserRole.STUDENT,
            title="Canvas login issue",
            description="Login fails after reset",
            status=ServiceStatus.PENDING,
            priority=ServicePriority.MEDIUM,
            category=ServiceCategory.SOFTWARE_ISSUE,
            department=None,
            ai_summary=None,
            ai_recommended_action=None,
            ai_missing_information=None,
            ai_reasoning=None,
            ai_processing_ms=None,
            manual_summary="Summary",
            manual_response="Response",
            manual_next_steps=["Wait 15 minutes."],
            ai_confidence=None,
            ai_trace=None,
            created_at=None,
            updated_at=None,
        )

        self.assertEqual(
            _manual_triage_success_message(ticket),
            "Manual triage saved for ticket 7. Status is now Pending.",
        )


if __name__ == "__main__":
    unittest.main()
