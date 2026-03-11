"""Tickets Table Component"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from loguru import logger
from nicegui import ui
from nicegui.elements.table import Table

from src.models import (
    ServiceCategory,
    ServicePriority,
    ServiceStatus,
    UserRole,
)
from src.schemas import TicketUpdateSchema
from src.schemas.schema import TicketResponseSchema
from src.services import TicketService

from .table_config import COLUMN_DEFAULTS, COLUMNS
from .table_utils import add_expandable_row, add_search

_ACTION_LABELS = {
    "start": "Start",
    "close": "Close",
}

_BADGE_COLORS = {
    "priority": {
        "High": "red",
        "Medium": "orange",
        "Low": "yellow",
    },
    "status": {
        "Open": "green",
        "Pending": "orange",
        "Closed": "red",
    },
}


def _coerce_enum[TEnum: StrEnum](enum_cls: type[TEnum], value: TEnum | str) -> TEnum:
    """Convert table JSON values back into the canonical enum values."""
    if isinstance(value, enum_cls):
        return value
    return enum_cls(str(value).strip().lower())


def _badge_color(column_name: str, value: Any) -> str:
    """Return the badge color for one rendered table value."""
    return _BADGE_COLORS.get(column_name, {}).get(str(value), "grey-5")


def _normalize_table_row(row: dict[str, Any]) -> dict[str, Any]:
    """Add display-only fields required by the custom table slots."""
    normalized_row = dict(row)
    normalized_row.update(_ACTION_LABELS)
    normalized_row["priority_color"] = _badge_color("priority", normalized_row.get("priority"))
    normalized_row["status_color"] = _badge_color("status", normalized_row.get("status"))
    return normalized_row


def _serialize_table_row(ticket: TicketResponseSchema) -> dict[str, Any]:
    """Serialize one ticket into a row consumable by the table slots."""
    return _normalize_table_row(ticket.model_dump(mode="json"))


def _serialize_table_rows(data: list[TicketResponseSchema]) -> list[dict[str, Any]]:
    """Serialize ticket data into rows consumable by the table slots."""
    return [_serialize_table_row(ticket) for ticket in data]


def _build_update_payload(row: dict[str, Any], status: ServiceStatus) -> TicketUpdateSchema:
    """Map one table row back into the update schema expected by the service layer."""
    return TicketUpdateSchema(
        id=int(row["id"]),
        requestor_name=str(row["requestor_name"]),
        requestor_email=str(row["requestor_email"]),
        user_role=_coerce_enum(UserRole, row["user_role"]),
        title=str(row["title"]),
        description=str(row["description"]),
        status=status,
        priority=_coerce_enum(ServicePriority, row["priority"]),
        category=_coerce_enum(ServiceCategory, row["category"]),
    )


def _sync_table_row(table: Table, updated_ticket: TicketResponseSchema) -> None:
    """Replace one row in the UI with the latest service response."""
    updated_row = _serialize_table_row(updated_ticket)
    ticket_id = updated_row["id"]
    table.update_rows(
        [updated_row if row["id"] == ticket_id else row for row in table.rows],
        clear_selection=False,
    )
    table.selected[:] = [updated_row if row["id"] == ticket_id else row for row in table.selected]
    table.update()


def ticket_table(title: str, data: list[TicketResponseSchema], service: TicketService) -> Table:
    """Service Desk Ticket Table Component

    Args:
        data (list[TicketResponseSchema]): Data that will be populated in the table
    """
    rows = _serialize_table_rows(data)
    with ui.table(
        title=title,
        columns=COLUMNS,
        column_defaults=COLUMN_DEFAULTS,
        rows=rows,
        row_key="id",
        selection="multiple",
        pagination=10,
    ).classes("w-full") as table:

        async def set_ticket_status(row: dict[str, Any], status: ServiceStatus) -> None:
            ticket_id = int(row["id"])
            current_status = _coerce_enum(ServiceStatus, row["status"])
            if current_status == status:
                logger.info("Ignoring ticket status update for ticket {} because it is already {}.", ticket_id, status)
                ui.notify(f"Ticket {ticket_id} is already {status.value.title()}.", color="warning")
                return

            logger.info(
                "Updating ticket {} status from {} to {} from the table UI.",
                ticket_id,
                current_status,
                status,
            )
            updated_ticket = await service.update_ticket(ticket_id, _build_update_payload(row, status))
            if updated_ticket is None:
                logger.warning("Unable to update ticket {} because it was not found.", ticket_id)
                ui.notify(f"Ticket {ticket_id} was not found.", color="negative")
                return

            _sync_table_row(table, updated_ticket)
            logger.info("Ticket {} status updated to {}.", ticket_id, updated_ticket.status)
            ui.notify(
                f"Ticket {ticket_id} moved to {updated_ticket.status.value.title()}.",
                color="positive",
            )

        table = add_search(table=table)
        table = add_expandable_row(table=table)
        table.on("ticket-start", handler=lambda e: set_ticket_status(e.args, ServiceStatus.PENDING))
        table.on("ticket-close", handler=lambda e: set_ticket_status(e.args, ServiceStatus.CLOSED))
    return table
