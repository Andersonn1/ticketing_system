"""AI Driven Service Page"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, Final
from uuid import uuid4

from fastapi import Depends
from loguru import logger
from nicegui import app, background_tasks, ui

from src.components import ticket_table
from src.components.ticket_table.ticket_table import _normalize_table_row, _serialize_table_rows
from src.core.theme import frame
from src.dependencies import get_ticket_service
from src.services import TicketService, TriageBatchResult

_TRIAGE_JOB_STORAGE_KEY: Final[str] = "ai_triage_job"
_TRIAGE_JOB_RUNNING: Final[str] = "running"
_TRIAGE_JOB_COMPLETED: Final[str] = "completed"


def _selected_ticket_ids(selected_rows: list[dict[str, Any]]) -> list[int]:
    """Extract selected ticket IDs from table rows."""
    return [int(row["id"]) for row in selected_rows if "id" in row]


def _triage_result_notification(result: TriageBatchResult) -> tuple[str, str]:
    """Build the user-facing triage completion message."""
    if result.failed:
        return (
            f"Triage completed for {len(result.completed)} ticket(s); {len(result.failed)} failed.",
            "warning",
        )
    return (f"AI triage completed for {len(result.completed)} ticket(s).", "positive")


def _set_local_ticket_statuses(table: Any, ticket_ids: list[int], status_label: str) -> None:
    """Update the rendered table rows for a set of ticket IDs without dropping other rows."""
    target_ids = set(ticket_ids)
    if not target_ids:
        return

    table.rows[:] = [
        _normalize_table_row({**row, "status": status_label}) if int(row["id"]) in target_ids else row
        for row in table.rows
    ]
    table.selected[:] = [
        next((row for row in table.rows if int(row["id"]) == int(selected_row["id"])), selected_row)
        for selected_row in table.selected
    ]
    table.update()


def _triage_job_state(storage: MutableMapping[str, Any]) -> dict[str, Any] | None:
    """Return the persisted AI triage state for the current user, if any."""
    state = storage.get(_TRIAGE_JOB_STORAGE_KEY)
    return state if isinstance(state, dict) else None


def _start_triage_job(storage: MutableMapping[str, Any], ticket_ids: list[int]) -> str:
    """Persist a running triage job so the page can resume it after navigation."""
    job_id = uuid4().hex
    storage[_TRIAGE_JOB_STORAGE_KEY] = {
        "job_id": job_id,
        "status": _TRIAGE_JOB_RUNNING,
        "ticket_ids": [int(ticket_id) for ticket_id in ticket_ids],
    }
    return job_id


def _finish_triage_job(
    storage: MutableMapping[str, Any],
    *,
    job_id: str,
    ticket_ids: list[int],
    result: TriageBatchResult,
    message: str,
    color: str,
) -> None:
    """Persist triage completion details when the same job is still active."""
    current = _triage_job_state(storage)
    if current is None or current.get("job_id") != job_id:
        logger.debug("Skipping AI triage completion write for stale job {}.", job_id)
        return

    storage[_TRIAGE_JOB_STORAGE_KEY] = {
        "job_id": job_id,
        "status": _TRIAGE_JOB_COMPLETED,
        "ticket_ids": [int(ticket_id) for ticket_id in ticket_ids],
        "completed": [int(ticket_id) for ticket_id in result.completed],
        "failed": {str(ticket_id): error for ticket_id, error in result.failed.items()},
        "message": message,
        "color": color,
    }


def _clear_triage_job(storage: MutableMapping[str, Any]) -> None:
    """Remove any persisted AI triage state for the current user."""
    storage.pop(_TRIAGE_JOB_STORAGE_KEY, None)


async def _run_triage_job(
    storage: MutableMapping[str, Any],
    service: TicketService,
    ticket_ids: list[int],
    *,
    job_id: str,
) -> None:
    """Execute AI triage outside the page lifecycle and persist only resumable state."""
    try:
        logger.info("Running background AI triage job {} for tickets: {}", job_id, ticket_ids)
        result = await service.triage_tickets(ticket_ids)
        message, color = _triage_result_notification(result)
        if result.failed:
            logger.warning(
                "Background AI triage job {} finished with partial failures. Completed: {}. Failed: {}.",
                job_id,
                result.completed,
                result.failed,
            )
        else:
            logger.info("Background AI triage job {} finished successfully for tickets: {}.", job_id, result.completed)
        _finish_triage_job(
            storage,
            job_id=job_id,
            ticket_ids=ticket_ids,
            result=result,
            message=message,
            color=color,
        )
    except Exception:
        logger.exception("Background AI triage job {} failed unexpectedly for tickets: {}", job_id, ticket_ids)
        _finish_triage_job(
            storage,
            job_id=job_id,
            ticket_ids=ticket_ids,
            result=TriageBatchResult(
                completed=[], failed={ticket_id: "unexpected failure" for ticket_id in ticket_ids}
            ),
            message="AI triage failed unexpectedly. Check the logs for details.",
            color="negative",
        )


def register() -> None:
    """Register the AI Process Page"""

    @ui.page("/ai-process")
    async def ai_page(service: TicketService = Depends(get_ticket_service)):
        logger.info("Loading AI page ticket data.")
        data = await service.list_tickets()
        logger.info("AI page loaded {} tickets.", len(data))
        user_storage = app.storage.user
        with frame("AI Assist"):
            table = ticket_table(title="AI-Assisted Triage", data=data, service=service)

            async def refresh_table() -> None:
                if table.is_deleted:
                    logger.debug("Skipping AI page refresh because the table was deleted.")
                    return
                logger.info("Refreshing AI page ticket table.")
                refreshed_rows = await service.list_tickets()
                table.rows = _serialize_table_rows(refreshed_rows)
                table.update()
                logger.info("AI page refresh complete with {} ticket rows.", len(refreshed_rows))

            async def sync_triage_job_state() -> None:
                state = _triage_job_state(user_storage)
                if state is None:
                    if not triage_button.is_deleted:
                        triage_button.enable()
                    return

                status = str(state.get("status", ""))
                if status == _TRIAGE_JOB_RUNNING:
                    if not triage_button.is_deleted:
                        triage_button.disable()
                    return
                if status != _TRIAGE_JOB_COMPLETED:
                    logger.warning("Ignoring AI triage job state with unknown status: {}", status)
                    _clear_triage_job(user_storage)
                    if not triage_button.is_deleted:
                        triage_button.enable()
                    return

                await refresh_table()
                if table.is_deleted:
                    return
                ui.notify(str(state.get("message", "AI triage finished.")), color=str(state.get("color", "positive")))
                _clear_triage_job(user_storage)
                if not triage_button.is_deleted:
                    triage_button.enable()

            async def triage_selected() -> None:
                current_state = _triage_job_state(user_storage)
                if current_state is not None and current_state.get("status") == _TRIAGE_JOB_RUNNING:
                    logger.warning("AI triage requested while another triage job is still running.")
                    ui.notify("AI triage is already running for this session.", color="warning")
                    triage_button.disable()
                    return

                selected_ids = _selected_ticket_ids(table.selected)
                if not selected_ids:
                    logger.warning("AI triage requested without any selected tickets.")
                    ui.notify("Select at least one ticket first.", color="warning")
                    return

                logger.info("Starting AI triage for selected tickets: {}", selected_ids)
                triage_button.disable()
                _set_local_ticket_statuses(table, selected_ids, "Pending")
                job_id = _start_triage_job(user_storage, selected_ids)
                background_tasks.create(
                    _run_triage_job(user_storage, service, selected_ids, job_id=job_id),
                    name=f"ai triage {job_id}",
                )
                logger.debug("AI triage button remains disabled while background job {} runs.", job_id)

            with ui.row().classes("items-center q-gutter-sm"):
                triage_button = ui.button("Run AI on Selected", on_click=triage_selected).props("color=primary")
                ui.button("Refresh", on_click=refresh_table).props("flat")
            ui.timer(1.0, sync_triage_job_state, immediate=False)
            await sync_triage_job_state()
        logger.success("Successfully Registered AI Page!")
