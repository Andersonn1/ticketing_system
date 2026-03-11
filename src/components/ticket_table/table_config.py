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
        "name": "title",
        "label": "Title",
        "field": "title",
        "required": True,
        "sortable": True,
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
        "name": "status",
        "label": "Status",
        "field": "status",
        "required": True,
        "sortable": True,
        "align": "center",
    },
    {
        "name": "priority",
        "label": "Priority",
        "field": "priority",
        "required": True,
        "sortable": True,
        "align": "center",
    },
    {
        "name": "requestor_name",
        "label": "Requestor Name",
        "field": "requestor_name",
        "required": True,
        "sortable": True,
        "align": "center",
    },
    {
        "name": "requestor_email",
        "label": "Requestor Email",
        "field": "requestor_email",
        "required": True,
        "sortable": True,
        "align": "center",
    },
    {
        "name": "user_role",
        "label": "User Type",
        "field": "user_role",
        "required": True,
        "sortable": True,
        "align": "center",
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
        "name": "start",
        "label": "Start",
        "field": "start",
        "align": "center",
        "sortable": False,
    },
    {
        "name": "close",
        "label": "Close",
        "field": "close",
        "align": "center",
        "sortable": False,
    },
]
