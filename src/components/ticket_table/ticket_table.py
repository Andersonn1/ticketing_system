"""Tickets Table Component"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

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


def _coerce_enum[TEnum: StrEnum](enum_cls: type[TEnum], value: TEnum | str) -> TEnum:
    """Convert table JSON values back into the canonical enum values."""
    if isinstance(value, enum_cls):
        return value
    return enum_cls(str(value).strip().lower())


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
    updated_row = updated_ticket.model_dump(mode="json")
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
    rows: list[dict[str, Any]] = [x.model_dump(mode="json") for x in data]
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
                ui.notify(f"Ticket {ticket_id} is already {status.value.title()}.", color="warning")
                return

            updated_ticket = await service.update_ticket(ticket_id, _build_update_payload(row, status))
            if updated_ticket is None:
                ui.notify(f"Ticket {ticket_id} was not found.", color="negative")
                return

            _sync_table_row(table, updated_ticket)
            ui.notify(
                f"Ticket {ticket_id} moved to {updated_ticket.status.value.title()}.",
                color="positive",
            )

        add_search(table=table)
        add_expandable_row(table=table)
        with table.add_slot("body-cell-priority"):
            with table.cell("priority"):
                ui.badge().props("""
                        :color="props.value == 'High' ? 'red' : props.value == 'Medium' ? 'orange' : 'yellow'"
                        :label="props.value"
                    """)
        with table.add_slot("body-cell-status"):
            with table.cell("status"):
                ui.badge().props("""
                        :color="props.value == 'Open' ? 'green' : props.value == 'Pending' ? 'orange' : 'red'"
                        :label="props.value"
                    """)
        with table.add_slot("body-cell-start"):
            with table.cell("start"):
                ui.button("Start").props("flat").on(
                    "click",
                    handler=lambda e: set_ticket_status(e.args, ServiceStatus.PENDING),
                    js_handler="() => emit(props.row)",
                )
        with table.add_slot("body-cell-close"):
            with table.cell("close"):
                ui.button("Close").props("flat").on(
                    "click",
                    handler=lambda e: set_ticket_status(e.args, ServiceStatus.CLOSED),
                    js_handler="() => emit(props.row)",
                )
    return table
