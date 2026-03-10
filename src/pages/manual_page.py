"""Manual Driven Ticket System Page"""

from __future__ import annotations

from loguru import logger
from nicegui import ui

from src.components import ticket_table
from src.services import ServiceTicketService
from src.core.theme import frame


def register() -> None:
    @ui.page("/manual")
    async def manual_page():
        data = await ServiceTicketService().list_tickets()
        logger.info("Registering Manual Page")
        with frame("Manual Ticketing Example"):
            ticket_table(title="Manual Ticketing Service", data=data)
        logger.success("Successfully Registered Manual Page!")
