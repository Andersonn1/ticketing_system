"""Home Page"""

from __future__ import annotations

from pathlib import Path

from loguru import logger
from nicegui import ui

from src.core.theme import frame

from .configs.home_config import (
    COMMON_REQUEST_AREAS,
    HEADER_SCRIPT_TAG,
    HOME_ACTIONS,
    HOME_FEATURES,
    HOME_STEPS,
    SUPPORT_EXPECTATIONS,
    HomeAction,
)

IMG_PATH = Path(__file__).parent / "configs/assets"


def _render_home_action(action: HomeAction) -> None:
    """Render one homepage call-to-action button."""
    props = "color=primary" if action.primary else "outline color=primary"
    ui.button(action.label, icon=action.icon, on_click=lambda href=action.href: ui.navigate.to(action.href)).props(
        props
    ).classes("min-w-[180px]")


def register() -> None:
    """Register the Home page"""

    @ui.page("/")
    def home_page():
        logger.info("Rendering home page.")
        ui.add_head_html(HEADER_SCRIPT_TAG)
        with frame("Help Desk"):
            with ui.column().classes("w-full max-w-7xl mx-auto gap-8 px-4 py-6 md:px-8"):
                with ui.card().classes("w-full p-8 gap-4 bg-slate-50"):
                    ui.label("Help Desk").classes("text-h3 md:text-h2 font-bold text-primary")
                    ui.label(
                        "Submit requests, coordinate support workflows, and manage issue resolution from one shared portal."
                    ).classes("text-body1 text-slate-700 max-w-3xl")
                    with ui.row().classes("w-full gap-3 items-center"):
                        for action in HOME_ACTIONS:
                            _render_home_action(action)

                with ui.column().classes("w-full gap-3"):
                    ui.label("Support capabilities").classes("text-h5 font-semibold")
                    with ui.row().classes("w-full gap-4 items-stretch"):
                        for feature in HOME_FEATURES:
                            with ui.card().classes("col flex-1 min-w-[220px] p-5 gap-3"):
                                ui.icon(feature.icon, color="primary").classes("text-3xl")
                                ui.label(feature.title).classes("text-h6 font-semibold")
                                ui.label(feature.description).classes("text-body2 text-slate-600")

                with ui.row().classes("w-full gap-4 items-stretch"):
                    with ui.card().classes("col flex-1 min-w-[320px] p-6 gap-4"):
                        ui.label("How support works").classes("text-h5 font-semibold")
                        for index, step in enumerate(HOME_STEPS, start=1):
                            icon = f"img:{IMG_PATH.as_posix().removeprefix('/')}/{str(index)}-solid.png"
                            with ui.row().classes("w-full items-start gap-3"):
                                ui.avatar(
                                    icon,
                                    color="primary",
                                    text_color="grey-11",
                                )
                                ui.label(step).classes("text-body2 text-slate-700")

                    with ui.card().classes("col flex-1 min-w-[320px] p-6 gap-4"):
                        ui.label("What to include").classes("text-h5 font-semibold")
                        ui.label("Common request areas").classes("text-subtitle2 font-medium text-slate-700")
                        for area in COMMON_REQUEST_AREAS:
                            ui.label(f"• {area}").classes("text-body2 text-slate-600")
                        ui.separator()
                        ui.label("Support expectations").classes("text-subtitle2 font-medium text-slate-700")
                        for expectation in SUPPORT_EXPECTATIONS:
                            ui.label(f"• {expectation}").classes("text-body2 text-slate-600")

                with ui.row().classes("w-full gap-4 items-stretch"):
                    with ui.card().classes("col flex-1 w-[400px] min-width[400px] max-width[400px] p-6 gap-4"):
                        ui.label("Support Schedule").classes("text-h5 font-semibold")
                        ui.html("<div id='calendar'></div>")
