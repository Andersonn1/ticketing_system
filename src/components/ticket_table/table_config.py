"""Ticket Table Configuration"""

from __future__ import annotations

from typing import Final

COLUMN_DEFAULTS: Final[dict[str, str]] = {
    "align": "left",
    "headerClasses": "uppercase text-primary",
}
COLUMNS: Final[list[dict[str, str | bool]]] = [
    {
        "name": "id",
        "label": "ID",
        "field": "id",
        "required": True,
        "sortable": False,
        "align": "center",
    },
    {
        "name": "urgency",
        "label": "Urgency",
        "field": "urgency",
        "required": True,
        "sortable": True,
        "align": "center",
    },
    {
        "name": "category",
        "label": "Category",
        "field": "category",
        "required": True,
        "sortable": True,
        "align": "center",
    },
    {
        "name": "description",
        "label": "Description",
        "field": "description",
        "required": True,
        "sortable": False,
    },
    {
        "name": "first_occurrence",
        "label": "Date Occurred",
        "field": "first_occurrence",
        "required": True,
        "sortable": True,
        "align": "center",
    },
    {
        "name": "received_error_message",
        "label": "Has Error Message",
        "field": "received_error_message",
        "required": True,
        "sortable": True,
        "align": "center",
    },
    {
        "name": "error_message_details",
        "label": "Error Details",
        "field": "error_message_details",
        "required": False,
        "sortable": False,
    },
    {
        "name": "created_at",
        "label": "Date Created",
        "field": "created_at",
        "required": True,
        "sortable": True,
        "align": "center",
    },
    {
        "name": "updated_at",
        "label": "Date Updated",
        "field": "updated_at",
        "required": True,
        "sortable": True,
        "align": "center",
    },
    {
        "name": "assignee",
        "label": "Assignee",
        "field": "assignee",
        "required": True,
        "sortable": True,
        "align": "center",
    },
    {"name": "delete", "label": "Delete", "align": "center"},
    {"name": "close", "label": "Close", "align": "center"},
]
