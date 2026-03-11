"""Manual request page helper tests."""

from __future__ import annotations

import unittest

from src.models import UserRole
from src.pages.manual_request_page import (
    _build_create_payload,
    _format_confirmation_message,
    _guidance_warnings,
)


class ManualRequestPageHelperTests(unittest.TestCase):
    """Verify request intake helper behavior."""

    def test_build_create_payload_trims_and_normalizes_valid_values(self) -> None:
        payload = _build_create_payload(
            {
                "requestor_name": "  Jane Student  ",
                "requestor_email": "  jane.student@example.edu  ",
                "user_role": "student",
                "title": "  Canvas login fails after reset  ",
                "description": "  Canvas rejects my login after a password reset even after I cleared cache.  ",
            }
        )

        self.assertEqual(payload.requestor_name, "Jane Student")
        self.assertEqual(payload.requestor_email, "jane.student@example.edu")
        self.assertEqual(payload.user_role, UserRole.STUDENT)
        self.assertEqual(payload.title, "Canvas login fails after reset")
        self.assertEqual(
            payload.description,
            "Canvas rejects my login after a password reset even after I cleared cache.",
        )

    def test_guidance_warnings_flags_generic_title(self) -> None:
        warnings = _guidance_warnings(
            {
                "requestor_name": "Jane Student",
                "requestor_email": "jane.student@example.edu",
                "user_role": "student",
                "title": "Help needed",
                "description": "Canvas rejects my login after a password reset and I already cleared cache and retried.",
            }
        )

        self.assertIn("Make the title more specific by naming the system, device, or exact error.", warnings)

    def test_guidance_warnings_flags_vague_description(self) -> None:
        warnings = _guidance_warnings(
            {
                "requestor_name": "Jane Student",
                "requestor_email": "jane.student@example.edu",
                "user_role": "student",
                "title": "Canvas login issue",
                "description": "Login fails after reset.",
            }
        )

        self.assertIn(
            "Add more detail to the description, including what you were doing and what you already tried.",
            warnings,
        )

    def test_confirmation_message_mentions_ticket_id(self) -> None:
        message = _format_confirmation_message(42)

        self.assertEqual(
            message,
            "Your request was submitted successfully. Ticket #42 is now in the support queue.",
        )


if __name__ == "__main__":
    unittest.main()
