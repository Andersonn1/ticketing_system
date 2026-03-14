"""Application Header Menu"""

from __future__ import annotations

from typing import Final

from nicegui import app, ui

NAV_LINKS: Final[tuple[tuple[str, str], ...]] = (
    ("Home", "/"),
    ("Submit Ticket", "/request"),
    ("Support Queue", "/manual"),
    ("AI Assist", "/ai-process"),
)


def header_menu() -> None:
    """Application Header Menu Component"""
    dark_mode = ui.dark_mode(
        value=app.storage.browser.get("dark_mode"),
        on_change=lambda e: ui.run_javascript(f"""
        fetch('/dark_mode', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{value: {e.value}}}),
        }});
    """),
    )
    for label, href in NAV_LINKS:
        ui.link(label, href).classes(replace="text-white").classes("font-bold")
    with ui.element().classes("max-[420px]:hidden").tooltip("Cycle theme mode through dark, light, and system/auto."):
        ui.button(icon="dark_mode", on_click=lambda: dark_mode.set_value(None)).props(
            "flat fab-mini color=white"
        ).bind_visibility_from(dark_mode, "value", value=True)
        ui.button(icon="light_mode", on_click=lambda: dark_mode.set_value(True)).props(
            "flat fab-mini color=white"
        ).bind_visibility_from(dark_mode, "value", value=False)
        ui.button(icon="brightness_auto", on_click=lambda: dark_mode.set_value(False)).props(
            "flat fab-mini color=white"
        ).bind_visibility_from(dark_mode, "value", lambda mode: mode is None)
