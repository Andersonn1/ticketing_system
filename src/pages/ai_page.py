"""AI Driven Ticket System Page"""

from __future__ import annotations

from nicegui import ui

from src.core.theme import frame


def register() -> None:
    @ui.page("/ai-process")
    def ai_page():
        with frame("AI Example"):
            ui.label("This is the ai example page.")
