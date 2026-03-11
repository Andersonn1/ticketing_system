"""AI Driven Ticket System Page"""

from __future__ import annotations

from fastapi import Depends
from loguru import logger
from nicegui import ui

from src.components import ticket_table
from src.core.theme import frame
from src.dependencies import get_ticket_service
from src.services import TicketService


def register() -> None:
    """Register the AI Process Page"""

    @ui.page("/ai-process")
    async def ai_page(service: TicketService = Depends(get_ticket_service)):
        logger.info("Registering AI Page")
        data = await service.list_tickets()
        with frame("AI Ticketing Example"):
            table = ticket_table(title="AI Ticketing Service", data=data, service=service)

            async def refresh_table() -> None:
                table.rows = [item.model_dump(mode="json") for item in await service.list_tickets()]
                table.update()

            async def triage_selected() -> None:
                selected_ids = [int(row["id"]) for row in table.selected if "id" in row]
                if not selected_ids:
                    ui.notify("Select at least one ticket first.", color="warning")
                    return

                triage_button.disable()
                try:
                    result = await service.triage_tickets(selected_ids)
                    await refresh_table()
                    if result.failed:
                        ui.notify(
                            f"Triage completed for {len(result.completed)} ticket(s); {len(result.failed)} failed.",
                            color="warning",
                        )
                    else:
                        ui.notify(
                            f"AI triage completed for {len(result.completed)} ticket(s).",
                            color="positive",
                        )
                finally:
                    triage_button.enable()

            with ui.row().classes("items-center q-gutter-sm"):
                triage_button = ui.button("Run AI on Selected", on_click=triage_selected).props("color=primary")
                ui.button("Refresh", on_click=refresh_table).props("flat")
        logger.success("Successfully Registered AI Page!")
