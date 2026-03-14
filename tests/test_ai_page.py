"""AI page helper tests."""

from __future__ import annotations

import unittest

from src.pages.ai_service_page import (
    _TRIAGE_JOB_STORAGE_KEY,
    _clear_triage_job,
    _finish_triage_job,
    _selected_ticket_ids,
    _start_triage_job,
    _triage_job_state,
    _triage_result_notification,
)
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

    def test_start_triage_job_persists_running_state(self) -> None:
        storage: dict[str, object] = {}

        job_id = _start_triage_job(storage, [7, 11])
        state = _triage_job_state(storage)

        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual(state["job_id"], job_id)
        self.assertEqual(state["status"], "running")
        self.assertEqual(state["ticket_ids"], [7, 11])

    def test_finish_triage_job_persists_completion_for_active_job(self) -> None:
        storage: dict[str, object] = {}
        job_id = _start_triage_job(storage, [7, 11])

        _finish_triage_job(
            storage,
            job_id=job_id,
            ticket_ids=[7, 11],
            result=TriageBatchResult(completed=[7], failed={11: "boom"}),
            message="done",
            color="warning",
        )
        state = _triage_job_state(storage)

        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual(state["status"], "completed")
        self.assertEqual(state["completed"], [7])
        self.assertEqual(state["failed"], {"11": "boom"})
        self.assertEqual(state["message"], "done")
        self.assertEqual(state["color"], "warning")

    def test_finish_triage_job_ignores_stale_job_updates(self) -> None:
        storage: dict[str, object] = {}
        stale_job_id = _start_triage_job(storage, [7])
        current_job_id = _start_triage_job(storage, [11])

        _finish_triage_job(
            storage,
            job_id=stale_job_id,
            ticket_ids=[7],
            result=TriageBatchResult(completed=[7], failed={}),
            message="stale",
            color="positive",
        )
        state = _triage_job_state(storage)

        self.assertEqual(
            state,
            {
                "job_id": current_job_id,
                "status": "running",
                "ticket_ids": [11],
            },
        )

    def test_clear_triage_job_removes_state(self) -> None:
        storage: dict[str, object] = {_TRIAGE_JOB_STORAGE_KEY: {"status": "running"}}

        _clear_triage_job(storage)

        self.assertIsNone(_triage_job_state(storage))


if __name__ == "__main__":
    unittest.main()
