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
        original_get_llm_client = dependencies.get_llm_client
        try:
            dependencies._get_session = fake_session_provider  # type: ignore[assignment]
            dependencies.get_llm_client = lambda: fake_client  # type: ignore[assignment]

            service = dependencies.get_ticket_service()

            self.assertIsInstance(service, TicketService)
            self.assertIs(service._session_provider, fake_session_provider)
            self.assertIs(service._llm_client, fake_client)
        finally:
            dependencies._get_session = original_get_session
            dependencies.get_llm_client = original_get_llm_client

    def test_get_llm_client_prefers_openai_when_api_key_is_present(self) -> None:
        class FakeSecret:
            def get_secret_value(self) -> str:
                return "sk-test"

        class FakeSettings:
            model_provider_api_key = FakeSecret()

        fake_client = object()
        original_get_settings = dependencies.get_settings
        try:
            dependencies.get_settings = lambda: FakeSettings()  # type: ignore[assignment]
            from src.llm import openai_client

            original_get_openai_client = openai_client.get_openai_client
            openai_client.get_openai_client = lambda: fake_client  # type: ignore[assignment]
            try:
                self.assertIs(dependencies.get_llm_client(), fake_client)
            finally:
                openai_client.get_openai_client = original_get_openai_client
        finally:
            dependencies.get_settings = original_get_settings

    def test_get_llm_client_falls_back_to_ollama_without_api_key(self) -> None:
        class FakeSettings:
            model_provider_api_key = None

        fake_client = object()
        original_get_settings = dependencies.get_settings
        try:
            dependencies.get_settings = lambda: FakeSettings()  # type: ignore[assignment]
            from src.llm import ollama_client

            original_get_ollama_client = ollama_client.get_ollama_client
            ollama_client.get_ollama_client = lambda: fake_client  # type: ignore[assignment]
            try:
                self.assertIs(dependencies.get_llm_client(), fake_client)
            finally:
                ollama_client.get_ollama_client = original_get_ollama_client
        finally:
            dependencies.get_settings = original_get_settings

    def test_page_registration_still_supports_dependency_injection(self) -> None:
        manual_request_page.register()
        manual_service_page.register()
        ai_service_page.register()


if __name__ == "__main__":
    unittest.main()
