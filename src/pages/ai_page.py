"""AI Driven Ticket System Page"""

from __future__ import annotations

from loguru import logger
from nicegui import ui

from src.components import load_mock_tickets, ticket_table
from src.core.theme import frame


def register() -> None:
    @ui.page("/ai-process")
    def ai_page():
        logger.info("Registering AI Page")
        data = load_mock_tickets()
        with frame("Manual Ticketing Example"):
            ticket_table(title="AI Ticketing Service", data=data)
        logger.success("Successfully Registered AI Page!")
