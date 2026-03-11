"""Ticket table helper tests."""

from __future__ import annotations

import unittest

from src.components.ticket_table.ticket_table import (
    _badge_color,
    _build_update_payload,
    _coerce_enum,
    _normalize_table_row,
    _serialize_table_row,
    _sync_table_row,
)
from src.models import ServiceCategory, ServicePriority, ServiceStatus, UserRole
from src.schemas import TicketResponseSchema


class FakeTable:
    """Minimal table double for row replacement tests."""

    def __init__(self, rows: list[dict], selected: list[dict]) -> None:
        self.rows = rows
        self.selected = selected
        self.update_calls = 0

    def update_rows(self, rows: list[dict], *, clear_selection: bool = True) -> None:
        self.rows[:] = rows
        if clear_selection:
            self.selected.clear()

    def update(self) -> None:
        self.update_calls += 1


class TicketTableHelperTests(unittest.TestCase):
    """Verify conversion between table rows and domain schemas."""

    def test_badge_color_maps_status_and_priority_values(self) -> None:
        self.assertEqual(_badge_color("status", "Open"), "green")
        self.assertEqual(_badge_color("priority", "High"), "red")
        self.assertEqual(_badge_color("priority", "Unknown"), "grey-5")

    def test_normalize_table_row_adds_action_and_badge_metadata(self) -> None:
        row = _normalize_table_row(
            {
                "id": 42,
                "status": "Pending",
                "priority": "Medium",
            }
        )

        self.assertEqual(row["start"], "Start")
        self.assertEqual(row["close"], "Close")
        self.assertEqual(row["status_color"], "orange")
        self.assertEqual(row["priority_color"], "orange")

    def test_coerce_enum_accepts_serialized_title_case_values(self) -> None:
        self.assertEqual(_coerce_enum(ServiceStatus, "Pending"), ServiceStatus.PENDING)
        self.assertEqual(_coerce_enum(ServicePriority, "Low"), ServicePriority.LOW)
        self.assertEqual(_coerce_enum(UserRole, "Student"), UserRole.STUDENT)

    def test_build_update_payload_restores_expected_enums(self) -> None:
        row = {
            "id": 42,
            "requestor_name": "Jane Student",
            "requestor_email": "jane@example.edu",
            "user_role": "Student",
            "title": "Canvas login issue",
            "description": "Login fails after reset",
            "status": "Open",
            "priority": "Low",
            "category": "Other",
        }

        payload = _build_update_payload(row, ServiceStatus.CLOSED)

        self.assertEqual(payload.id, 42)
        self.assertEqual(payload.status, ServiceStatus.CLOSED)
        self.assertEqual(payload.priority, ServicePriority.LOW)
        self.assertEqual(payload.category, ServiceCategory.OTHER)
        self.assertEqual(payload.user_role, UserRole.STUDENT)

    def test_sync_table_row_replaces_matching_row_without_clearing_selection(self) -> None:
        original_row = {
            "id": 7,
            "requestor_name": "Jane Student",
            "requestor_email": "jane@example.edu",
            "user_role": "Student",
            "title": "Canvas login issue",
            "description": "Login fails after reset",
            "status": "Open",
            "priority": "Low",
            "category": "Other",
            "ai_summary": None,
            "ai_response": None,
            "ai_next_steps": [],
            "ai_confidence": None,
            "ai_trace": None,
            "created_at": None,
            "updated_at": None,
        }
        table = FakeTable(rows=[original_row.copy()], selected=[original_row.copy()])
        updated_ticket = TicketResponseSchema(
            id=7,
            requestor_name="Jane Student",
            requestor_email="jane@example.edu",
            user_role=UserRole.STUDENT,
            title="Canvas login issue",
            description="Login fails after reset",
            status=ServiceStatus.CLOSED,
            priority=ServicePriority.LOW,
            category=ServiceCategory.OTHER,
            ai_summary=None,
            ai_response=None,
            ai_next_steps=[],
            ai_confidence=None,
            ai_trace=None,
            created_at=None,
            updated_at=None,
        )

        _sync_table_row(table, updated_ticket)

        self.assertEqual(table.rows[0]["status"], "Closed")
        self.assertEqual(table.rows[0]["close"], "Close")
        self.assertEqual(table.rows[0]["status_color"], "red")
        self.assertEqual(table.selected[0]["status"], "Closed")
        self.assertEqual(table.update_calls, 1)

    def test_serialize_table_row_preserves_display_values_and_metadata(self) -> None:
        ticket = TicketResponseSchema(
            id=7,
            requestor_name="Jane Student",
            requestor_email="jane@example.edu",
            user_role=UserRole.STUDENT,
            title="Canvas login issue",
            description="Login fails after reset",
            status=ServiceStatus.OPEN,
            priority=ServicePriority.HIGH,
            category=ServiceCategory.OTHER,
            ai_summary=None,
            ai_response=None,
            ai_next_steps=[],
            ai_confidence=None,
            ai_trace=None,
            created_at=None,
            updated_at=None,
        )

        row = _serialize_table_row(ticket)

        self.assertEqual(row["status"], "Open")
        self.assertEqual(row["priority"], "High")
        self.assertEqual(row["start"], "Start")
        self.assertEqual(row["priority_color"], "red")


if __name__ == "__main__":
    unittest.main()
