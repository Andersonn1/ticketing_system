"""Application Header Menu"""

from __future__ import annotations

from nicegui import app, ui


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
    ui.link("Home", "/").classes(replace="text-white").classes("font-bold")
    ui.link("Submit Ticket", "/request").classes(replace="text-white").classes("font-bold")
    ui.link("Manual Process", "/manual").classes(replace="text-white").classes("font-bold")
    ui.link("AI Process", "/ai-process").classes(replace="text-white").classes("font-bold")
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
