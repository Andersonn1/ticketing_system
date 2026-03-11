"""AI page helper tests."""

from __future__ import annotations

import unittest

from src.pages.ai_service_page import _selected_ticket_ids, _triage_result_notification
from src.services import TriageBatchResult


class AIPageHelperTests(unittest.TestCase):
    """Verify AI page helpers produce stable user-facing behavior."""

    def test_selected_ticket_ids_skips_rows_without_ids(self) -> None:
        selected_ids = _selected_ticket_ids([{"id": "7"}, {"title": "missing-id"}, {"id": 11}])

        self.assertEqual(selected_ids, [7, 11])

    def test_triage_result_notification_reports_partial_failure(self) -> None:
        message, color = _triage_result_notification(TriageBatchResult(completed=[7], failed={11: "boom"}))

        self.assertEqual(message, "Triage completed for 1 ticket(s); 1 failed.")
        self.assertEqual(color, "warning")

    def test_triage_result_notification_reports_success(self) -> None:
        message, color = _triage_result_notification(TriageBatchResult(completed=[7, 11], failed={}))

        self.assertEqual(message, "AI triage completed for 2 ticket(s).")
        self.assertEqual(color, "positive")


if __name__ == "__main__":
    unittest.main()
