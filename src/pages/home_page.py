"""Home Page"""

from __future__ import annotations

from nicegui import ui

from src.core.theme import frame


def register() -> None:
    @ui.page("/")
    def home_page():
        with frame("- Page B -"):
            ui.label("This is the home page.")
