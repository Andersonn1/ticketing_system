"""Tickets Table Component"""

from __future__ import annotations

from typing import Any

from nicegui import ui

from src.schemas.service_ticket import ServiceTicket

from .table_config import COLUMN_DEFAULTS, COLUMNS


def ticket_table(title: str, data: list[ServiceTicket]) -> None:
    """Service Desk Ticket Table Component

    Args:
        data (list[ServiceTicket]): Data that will be populated in the table
    """
    rows: list[dict[str, Any]] = [x.model_dump() for x in data]
    with ui.table(
        title=title,
        columns=COLUMNS,
        column_defaults=COLUMN_DEFAULTS,
        rows=rows,
        selection="multiple",
        pagination=10,
    ).classes("w-full") as table:
        with table.add_slot("top-right"):
            with (
                ui.input(placeholder="Search")
                .props("type=search")
                .bind_value(table, "filter")
                .add_slot("append")
            ):
                ui.icon("search")
        with table.add_slot("body-cell-urgency"):
            with table.cell("urgency"):
                ui.badge().props("""
                        :color="props.value == 'High' ? 'red' : props.value == 'Medium' ? 'orange' : 'yellow'"
                        :label="props.value"
                    """)
        with table.add_slot("body-cell-delete"):
            with table.cell("delete"):
                ui.button("Delete").props("flat").on(
                    "click",
                    js_handler="() => emit(props.row.urgency)",
                    handler=lambda e: ui.notify(e.args),
                )
        with table.add_slot("body-cell-close"):
            with table.cell("close"):
                ui.button("Close").props("flat").on(
                    "click",
                    js_handler="() => emit(props.row.urgency)",
                    handler=lambda e: table.remove_rows(table.selected),
                )
