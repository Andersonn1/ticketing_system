"""Application Theme"""

from __future__ import annotations

from contextlib import contextmanager

from nicegui import ui

from src.core.header_menu import header_menu
from src.core.settings import get_settings

settings = get_settings()


@contextmanager
def frame(navigation_title: str):
    """Custom page frame to share the same styling and behavior across all pages"""
    ui.colors(
        primary="#1976d2",
        primary_light="#42a5f5",
        primary_dark="#1565c0",
        secondary="#9c27b0",
        secondary_light="#ba68c8",
        secondary_dark="#7b1fa2",
        accent="#111B1E",
        info="#0288d1",
        info_light="#03a9f4",
        info_dark="#01579b",
        warning="#ed6c02",
        warning_light="#ff9800",
        warning_dark="e65100",
        error="#d32f2f",
        error_light="#ef5350",
        error_dark="#c62828",
    )
    with ui.header().classes("items-center"):
        ui.label(settings.app_name).classes("font-bold")
        ui.space()
        ui.label(navigation_title).classes("font-bold")
        ui.space()
        with ui.row(align_items="center"):
            header_menu()
    yield
