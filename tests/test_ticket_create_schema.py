"""Ticket create schema validation tests."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from src.models import UserRole
from src.schemas import TicketCreateSchema


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "requestor_name": "Jane Student",
        "requestor_email": "jane.student@example.edu",
        "user_role": UserRole.STUDENT,
        "title": "Canvas login fails after reset",
        "description": "Canvas still rejects my login after I reset my password and restarted the browser.",
    }
    payload.update(overrides)
    return payload


class TicketCreateSchemaTests(unittest.TestCase):
    """Verify create-time ticket validation rules."""

    def test_valid_payload_is_trimmed(self) -> None:
        payload = TicketCreateSchema.model_validate(
            _valid_payload(
                requestor_name="  Jane Student  ",
                requestor_email="  jane.student@example.edu  ",
                title="  Canvas login fails after reset  ",
                description="  Canvas rejects my login after a password reset and browser restart.  ",
            )
        )

        self.assertEqual(payload.requestor_name, "Jane Student")
        self.assertEqual(payload.requestor_email, "jane.student@example.edu")
        self.assertEqual(payload.title, "Canvas login fails after reset")
        self.assertEqual(payload.description, "Canvas rejects my login after a password reset and browser restart.")

    def test_blank_name_is_rejected(self) -> None:
        with self.assertRaises(ValidationError) as context:
            TicketCreateSchema.model_validate(_valid_payload(requestor_name=""))

        self.assertEqual(context.exception.errors()[0]["msg"], "Value error, Enter your name.")

    def test_whitespace_only_description_is_rejected(self) -> None:
        with self.assertRaises(ValidationError) as context:
            TicketCreateSchema.model_validate(_valid_payload(description="    "))

        self.assertEqual(context.exception.errors()[0]["msg"], "Value error, Enter a description of the issue.")

    def test_invalid_email_is_rejected(self) -> None:
        with self.assertRaises(ValidationError) as context:
            TicketCreateSchema.model_validate(_valid_payload(requestor_email="not-an-email"))

        self.assertEqual(context.exception.errors()[0]["msg"], "Value error, Enter a valid email address.")

    def test_overlong_title_is_rejected(self) -> None:
        with self.assertRaises(ValidationError) as context:
            TicketCreateSchema.model_validate(_valid_payload(title="x" * 126))

        self.assertEqual(
            context.exception.errors()[0]["msg"], "Value error, Title must be between 8 and 125 characters."
        )

    def test_short_title_is_rejected(self) -> None:
        with self.assertRaises(ValidationError) as context:
            TicketCreateSchema.model_validate(_valid_payload(title="Printer"))

        self.assertEqual(
            context.exception.errors()[0]["msg"], "Value error, Title must be between 8 and 125 characters."
        )

    def test_short_description_is_rejected(self) -> None:
        with self.assertRaises(ValidationError) as context:
            TicketCreateSchema.model_validate(_valid_payload(description="Need help ASAP."))

        self.assertEqual(
            context.exception.errors()[0]["msg"],
            "Value error, Description must be between 20 and 4000 characters.",
        )


if __name__ == "__main__":
    unittest.main()
