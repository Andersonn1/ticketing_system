"""Manual triage modal for the pre-AI helpdesk workflow."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from typing import Any

from loguru import logger
from nicegui import ui
from pydantic import ValidationError

from src.models import ServiceCategory, ServicePriority, ServiceStatus
from src.schemas import ManualTriageSchema, TicketResponseSchema
from src.services import TicketService


def _labelize_enum_value(value: str) -> str:
    """Convert enum values to readable UI labels."""
    return value.replace("_", " ").title()


def _coerce_enum[TEnum: StrEnum](enum_cls: type[TEnum], value: TEnum | str) -> TEnum:
    """Convert serialized table values back into canonical enum members."""
    if isinstance(value, enum_cls):
        return value
    return enum_cls(str(value).strip().lower().replace(" ", "_"))


def _manual_triage_enabled(row: dict[str, Any]) -> bool:
    """Return whether a row can be manually triaged."""
    return _coerce_enum(ServiceStatus, row["status"]) in {ServiceStatus.OPEN, ServiceStatus.PENDING}


def _manual_triage_status_options(row: dict[str, Any]) -> dict[str, str]:
    """Return the status options allowed for one table row."""
    if not _manual_triage_enabled(row):
        return {}
    return {
        ServiceStatus.PENDING.value: ServiceStatus.PENDING.value.title(),
        ServiceStatus.CLOSED.value: ServiceStatus.CLOSED.value.title(),
    }


def _manual_triage_form_defaults(row: dict[str, Any]) -> dict[str, str]:
    """Build initial form values from one serialized table row."""
    current_status = _coerce_enum(ServiceStatus, row["status"])
    return {
        "summary": str(row.get("manual_summary") or ""),
        "response": str(row.get("manual_response") or ""),
        "next_steps": "\n".join(str(step) for step in row.get("manual_next_steps") or []),
        "priority": _coerce_enum(ServicePriority, row["priority"]).value,
        "category": _coerce_enum(ServiceCategory, row["category"]).value,
        "status": (current_status if current_status == ServiceStatus.PENDING else ServiceStatus.PENDING).value,
    }


def _build_manual_triage_payload(row: dict[str, Any], form_values: dict[str, Any]) -> ManualTriageSchema:
    """Convert modal form values into the manual triage schema."""
    del row
    next_steps_text = str(form_values.get("next_steps") or "")
    return ManualTriageSchema(
        summary=str(form_values.get("summary") or "").strip(),
        response=str(form_values.get("response") or "").strip(),
        next_steps=[step.strip() for step in next_steps_text.splitlines()],
        priority=_coerce_enum(ServicePriority, str(form_values.get("priority") or "")),
        category=_coerce_enum(ServiceCategory, str(form_values.get("category") or "")),
        status=_coerce_enum(ServiceStatus, str(form_values.get("status") or "")),
    )


def _manual_triage_success_message(ticket: TicketResponseSchema) -> str:
    """Build the user-facing success message after a manual triage save."""
    return f"Manual triage saved for ticket {ticket.id}. Status is now {ticket.status.value.title()}."


def create_manual_triage_opener(
    *,
    service: TicketService,
    on_ticket_updated: Callable[[TicketResponseSchema], None],
) -> Callable[[dict[str, Any]], None]:
    """Create the reusable modal opener used by the ticket table row action."""
    current_row: dict[str, Any] | None = None

    with ui.dialog().props("persistent") as dialog, ui.card().classes("w-[min(92vw,1100px)] p-6 gap-4"):
        ui.label("Manual Triage").classes("text-h5 font-bold")
        ui.label(
            "Capture the pre-AI helpdesk workflow by documenting the worker's summary, response, and next steps."
        ).classes("text-body2 text-slate-600")

        with ui.row().classes("w-full items-start gap-6"):
            with ui.card().classes("w-full max-w-md p-4 gap-3"):
                ui.label("Original Request").classes("text-h6 font-semibold")
                requestor_label = ui.label().classes("text-body2")
                requestor_email = ui.label().classes("text-body2")
                requestor_role = ui.label().classes("text-body2")
                request_title = ui.label().classes("text-subtitle1 font-medium")
                request_description = ui.label().classes("text-body2 whitespace-pre-wrap")

            with ui.column().classes("w-full gap-3"):
                summary_input = (
                    ui.textarea(label="Manual Summary", on_change=lambda _: apply_validation_feedback())
                    .props("outlined autogrow")
                    .classes("w-full")
                )
                summary_error = ui.label().classes("text-negative text-sm")
                summary_error.set_visibility(False)

                response_input = (
                    ui.textarea(label="Requester Response", on_change=lambda _: apply_validation_feedback())
                    .props("outlined autogrow")
                    .classes("w-full")
                )
                response_error = ui.label().classes("text-negative text-sm")
                response_error.set_visibility(False)

                next_steps_input = (
                    ui.textarea(label="Next Steps", on_change=lambda _: apply_validation_feedback())
                    .props("outlined autogrow")
                    .classes("w-full")
                )
                ui.label("Enter one next step per line.").classes("text-xs text-slate-500")
                next_steps_error = ui.label().classes("text-negative text-sm")
                next_steps_error.set_visibility(False)

                with ui.row().classes("w-full gap-4"):
                    priority_input = (
                        ui.select(
                            {priority.value: _labelize_enum_value(priority.value) for priority in ServicePriority},
                            label="Priority",
                            on_change=lambda _: apply_validation_feedback(),
                        )
                        .props("outlined")
                        .classes("w-full")
                    )
                    category_input = (
                        ui.select(
                            {category.value: _labelize_enum_value(category.value) for category in ServiceCategory},
                            label="Category",
                            on_change=lambda _: apply_validation_feedback(),
                        )
                        .props("outlined")
                        .classes("w-full")
                    )

                with ui.row().classes("w-full gap-4 items-end"):
                    status_input = ui.select(
                        options={status.value: _labelize_enum_value(status.value) for status in ServiceStatus},
                        label="Status",
                        on_change=lambda _: apply_validation_feedback(),
                    ).props("outlined")
                    status_error = ui.label().classes("text-negative text-sm")
                    status_error.set_visibility(False)

        with ui.row().classes("justify-end gap-3 w-full"):
            cancel_button = ui.button("Cancel", on_click=dialog.close).props("flat")
            save_button = ui.button("Save Manual Triage")

    error_labels = {
        "summary": summary_error,
        "response": response_error,
        "next_steps": next_steps_error,
        "status": status_error,
    }

    controls = {
        "summary": summary_input,
        "response": response_input,
        "next_steps": next_steps_input,
        "priority": priority_input,
        "category": category_input,
        "status": status_input,
    }

    def _form_state() -> dict[str, Any]:
        return {name: control.value for name, control in controls.items()}

    def apply_validation_feedback() -> dict[str, str]:
        errors: dict[str, str] = {}
        if current_row is None:
            return errors
        try:
            _build_manual_triage_payload(current_row, _form_state())
        except ValidationError as exc:
            for error in exc.errors():
                location = error.get("loc", ())
                if not location:
                    continue
                field_name = str(location[0])
                errors[field_name] = str(error["msg"])

        for field_name, label in error_labels.items():
            message = errors.get(field_name, "")
            label.set_text(message)
            label.set_visibility(bool(message))

        if errors:
            save_button.disable()
        else:
            save_button.enable()
        return errors

    async def submit_manual_triage() -> None:
        nonlocal current_row
        if current_row is None:
            return

        errors = apply_validation_feedback()
        if errors:
            logger.warning("Manual triage submission blocked by validation errors: {}", errors)
            ui.notify("Fix the highlighted manual triage fields before saving.", color="warning")
            return

        save_button.disable()
        cancel_button.disable()
        ticket_id = int(current_row["id"])
        logger.info("Submitting manual triage for ticket {}.", ticket_id)
        try:
            payload = _build_manual_triage_payload(current_row, _form_state())
            updated_ticket = await service.manual_triage_ticket(ticket_id, payload)
        except ValidationError as exc:
            logger.warning("Manual triage validation failed unexpectedly for ticket {}: {}", ticket_id, exc)
            apply_validation_feedback()
            ui.notify("Fix the highlighted manual triage fields before saving.", color="warning")
            return
        except ValueError as exc:
            logger.warning("Manual triage save rejected for ticket {}: {}", ticket_id, exc)
            ui.notify(str(exc), color="warning")
            return
        except Exception:
            logger.exception("Manual triage save failed unexpectedly for ticket {}.", ticket_id)
            ui.notify("Manual triage could not be saved. Please try again.", color="negative")
            raise
        finally:
            cancel_button.enable()
            apply_validation_feedback()

        if updated_ticket is None:
            ui.notify(f"Ticket {ticket_id} was not found.", color="negative")
            return

        on_ticket_updated(updated_ticket)
        current_row = None
        dialog.close()
        ui.notify(_manual_triage_success_message(updated_ticket), color="positive")

    def open_modal(row: dict[str, Any]) -> None:
        nonlocal current_row
        if not _manual_triage_enabled(row):
            ui.notify("Closed tickets cannot be manually triaged.", color="warning")
            return

        current_row = dict(row)
        defaults = _manual_triage_form_defaults(current_row)

        requestor_label.set_text(f"Requestor: {current_row['requestor_name']}")
        requestor_email.set_text(f"Email: {current_row['requestor_email']}")
        requestor_role.set_text(f"Role: {current_row['user_role']}")
        request_title.set_text(f"Title: {current_row['title']}")
        request_description.set_text(str(current_row["description"]))

        summary_input.value = defaults["summary"]
        response_input.value = defaults["response"]
        next_steps_input.value = defaults["next_steps"]
        priority_input.value = defaults["priority"]
        category_input.value = defaults["category"]
        status_input.options = _manual_triage_status_options(current_row)
        status_input.value = defaults["status"]
        apply_validation_feedback()
        dialog.open()

    save_button.on_click(submit_manual_triage)
    return open_modal
