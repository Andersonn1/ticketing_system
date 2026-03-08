"""Manual Driven Ticket System Page"""

from __future__ import annotations

from nicegui import ui

from src.core.theme import frame


def register() -> None:
    @ui.page("/manual")
    def manual_page():
        with frame("Manual Example"):
            ui.label("This is the manual example page.")
