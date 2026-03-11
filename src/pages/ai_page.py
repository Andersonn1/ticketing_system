"""AI Driven Ticket System Page"""

from __future__ import annotations

from typing import Any

from fastapi import Depends
from loguru import logger
from nicegui import ui

from src.components import ticket_table
from src.components.ticket_table.ticket_table import _normalize_table_row, _serialize_table_rows
from src.core.theme import frame
from src.dependencies import get_ticket_service
from src.services import TicketService, TriageBatchResult


def _selected_ticket_ids(selected_rows: list[dict[str, Any]]) -> list[int]:
    """Extract selected ticket IDs from table rows."""
    return [int(row["id"]) for row in selected_rows if "id" in row]


def _triage_result_notification(result: TriageBatchResult) -> tuple[str, str]:
    """Build the user-facing triage completion message."""
    if result.failed:
        return (
            f"Triage completed for {len(result.completed)} ticket(s); {len(result.failed)} failed.",
            "warning",
        )
    return (f"AI triage completed for {len(result.completed)} ticket(s).", "positive")


def _set_local_ticket_statuses(table: Any, ticket_ids: list[int], status_label: str) -> None:
    """Update the rendered table rows for a set of ticket IDs without dropping other rows."""
    target_ids = set(ticket_ids)
    if not target_ids:
        return

    table.rows[:] = [
        _normalize_table_row({**row, "status": status_label}) if int(row["id"]) in target_ids else row
        for row in table.rows
    ]
    table.selected[:] = [
        next((row for row in table.rows if int(row["id"]) == int(selected_row["id"])), selected_row)
        for selected_row in table.selected
    ]
    table.update()


def register() -> None:
    """Register the AI Process Page"""

    @ui.page("/ai-process")
    async def ai_page(service: TicketService = Depends(get_ticket_service)):
        logger.info("Loading AI page ticket data.")
        data = await service.list_tickets()
        logger.info("AI page loaded {} tickets.", len(data))
        with frame("AI Ticketing Example"):
            table = ticket_table(title="AI Ticketing Service", data=data, service=service)

            async def refresh_table() -> None:
                logger.info("Refreshing AI page ticket table.")
                refreshed_rows = await service.list_tickets()
                table.rows = _serialize_table_rows(refreshed_rows)
                table.update()
                logger.info("AI page refresh complete with {} ticket rows.", len(refreshed_rows))

            async def triage_selected() -> None:
                selected_ids = _selected_ticket_ids(table.selected)
                if not selected_ids:
                    logger.warning("AI triage requested without any selected tickets.")
                    ui.notify("Select at least one ticket first.", color="warning")
                    return

                logger.info("Starting AI triage for selected tickets: {}", selected_ids)
                triage_button.disable()
                _set_local_ticket_statuses(table, selected_ids, "Pending")
                try:
                    result = await service.triage_tickets(selected_ids)
                    await refresh_table()
                    message, color = _triage_result_notification(result)
                    if result.failed:
                        logger.warning(
                            "AI triage finished with partial failures. Completed: {}. Failed: {}.",
                            result.completed,
                            result.failed,
                        )
                    else:
                        logger.info("AI triage finished successfully for tickets: {}", result.completed)
                    ui.notify(message, color=color)
                except Exception:
                    logger.exception("AI triage failed unexpectedly for selected tickets: {}", selected_ids)
                    ui.notify("AI triage failed unexpectedly. Check the logs for details.", color="negative")
                    await refresh_table()
                    raise
                finally:
                    triage_button.enable()
                    logger.debug("AI triage button re-enabled.")

            with ui.row().classes("items-center q-gutter-sm"):
                triage_button = ui.button("Run AI on Selected", on_click=triage_selected).props("color=primary")
                ui.button("Refresh", on_click=refresh_table).props("flat")
        logger.success("Successfully Registered AI Page!")
