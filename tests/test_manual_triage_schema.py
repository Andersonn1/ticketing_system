"""Manual triage schema validation tests."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from src.models import ServiceCategory, ServicePriority, ServiceStatus
from src.schemas import ManualTriageSchema


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "summary": "Canvas login issue after a morning password reset.",
        "response": "We confirmed the account is active and advised the student about the sync delay.",
        "next_steps": ["Wait 15 minutes for credential sync.", "Retry Canvas after clearing browser cache."],
        "priority": ServicePriority.MEDIUM,
        "category": ServiceCategory.SOFTWARE_ISSUE,
        "status": ServiceStatus.PENDING,
    }
    payload.update(overrides)
    return payload


class ManualTriageSchemaTests(unittest.TestCase):
    """Verify manual triage payload validation."""

    def test_valid_payload_is_normalized(self) -> None:
        payload = ManualTriageSchema.model_validate(
            _valid_payload(
                summary="  Canvas login issue after a morning password reset.  ",
                response="  We confirmed the account is active and advised the student about the sync delay.  ",
                next_steps=[
                    "  Wait 15 minutes for credential sync.  ",
                    "  Retry Canvas after clearing browser cache.  ",
                ],
            )
        )

        self.assertEqual(payload.summary, "Canvas login issue after a morning password reset.")
        self.assertEqual(
            payload.response,
            "We confirmed the account is active and advised the student about the sync delay.",
        )
        self.assertEqual(
            payload.next_steps,
            ["Wait 15 minutes for credential sync.", "Retry Canvas after clearing browser cache."],
        )

    def test_blank_summary_is_rejected(self) -> None:
        with self.assertRaises(ValidationError) as context:
            ManualTriageSchema.model_validate(_valid_payload(summary="   "))

        self.assertEqual(context.exception.errors()[0]["msg"], "Value error, Enter a triage summary.")

    def test_blank_response_is_rejected(self) -> None:
        with self.assertRaises(ValidationError) as context:
            ManualTriageSchema.model_validate(_valid_payload(response="   "))

        self.assertEqual(context.exception.errors()[0]["msg"], "Value error, Enter a response for the requester.")

    def test_empty_next_steps_are_rejected(self) -> None:
        with self.assertRaises(ValidationError) as context:
            ManualTriageSchema.model_validate(_valid_payload(next_steps=["   ", ""]))

        self.assertEqual(context.exception.errors()[0]["msg"], "Value error, Enter at least one next step.")

    def test_invalid_status_is_rejected(self) -> None:
        with self.assertRaises(ValidationError) as context:
            ManualTriageSchema.model_validate(_valid_payload(status=ServiceStatus.OPEN))

        self.assertEqual(
            context.exception.errors()[0]["msg"],
            "Value error, Manual triage status must be Pending or Closed.",
        )


if __name__ == "__main__":
    unittest.main()
