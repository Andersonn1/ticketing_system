"""Home Page"""

from __future__ import annotations

from loguru import logger
from nicegui import ui

from src.core.theme import frame


def register() -> None:
    """Register the Home page"""

    @ui.page("/")
    def home_page():
        logger.info("Rendering home page.")
        with frame("Welcome to IT Support System"):
            ui.label("This is the home page.")
