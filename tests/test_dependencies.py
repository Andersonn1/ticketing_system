"""Dependency composition tests."""

from __future__ import annotations

import unittest

from src import dependencies
from src.pages import ai_service_page, manual_request_page, manual_service_page
from src.services import TicketService


class DependencyProviderTests(unittest.TestCase):
    """Verify app-facing providers compose shared services consistently."""

    def test_get_ticket_service_builds_ticket_service_from_providers(self) -> None:
        fake_session_provider = object()
        fake_client = object()
        original_get_session = dependencies._get_session
        original_get_ollama_client = dependencies.get_ollama_client
        try:
            dependencies._get_session = fake_session_provider  # type: ignore[assignment]
            dependencies.get_ollama_client = lambda: fake_client  # type: ignore[assignment]

            service = dependencies.get_ticket_service()

            self.assertIsInstance(service, TicketService)
            self.assertIs(service._session_provider, fake_session_provider)
            self.assertIs(service._ollama_client, fake_client)
        finally:
            dependencies._get_session = original_get_session
            dependencies.get_ollama_client = original_get_ollama_client

    def test_page_registration_still_supports_dependency_injection(self) -> None:
        manual_request_page.register()
        manual_service_page.register()
        ai_service_page.register()


if __name__ == "__main__":
    unittest.main()
