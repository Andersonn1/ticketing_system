"""Manual Driven Ticket System Page"""

from __future__ import annotations

from fastapi import Depends
from loguru import logger
from nicegui import ui

from src.components import ticket_table
from src.core.theme import frame
from src.dependencies import get_ticket_service
from src.services import TicketService


def register() -> None:
    """Register the Manual Process Page"""

    @ui.page("/manual")
    async def manual_page(service: TicketService = Depends(get_ticket_service)):
        data = await service.list_tickets()
        logger.info("Registering Manual Page")
        with frame("Manual Ticketing Example"):
            ticket_table(title="Manual Ticketing Service", data=data, service=service)
        logger.success("Successfully Registered Manual Page!")
