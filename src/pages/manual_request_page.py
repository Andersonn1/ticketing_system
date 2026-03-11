"""Help Desk Ticket Form"""

from __future__ import annotations

from typing import Any

from fastapi import Depends
from loguru import logger
from nicegui import ui
from pydantic import ValidationError

from src.core.theme import frame
from src.dependencies import get_ticket_service
from src.models import UserRole
from src.schemas import TicketCreateSchema
from src.services import TicketService

_FORM_DEFAULTS = {
    "requestor_name": "",
    "requestor_email": "",
    "user_role": None,
    "title": "",
    "description": "",
}

_FIELD_HELPERS = {
    "requestor_name": "Use your full name so the support team can identify the request.",
    "requestor_email": "Enter the email address where support should contact you.",
    "user_role": "Choose the role that best matches your relationship to the school.",
    "title": "Name the system, device, or error to make triage faster.",
    "description": "Explain what happened, what you expected, and anything you already tried.",
}

_GENERIC_TITLES = {
    "help needed",
    "issue",
    "problem",
    "support request",
    "ticket request",
    "need help",
    "assistance",
    "broken",
}


def _normalized_form_values(form_data: dict[str, Any]) -> dict[str, Any]:
    """Trim text values before validation or user guidance checks."""
    return {key: value.strip() if isinstance(value, str) else value for key, value in form_data.items()}


def _build_create_payload(form_data: dict[str, Any]) -> TicketCreateSchema:
    """Build the canonical create-ticket payload from raw form values."""
    normalized = _normalized_form_values(form_data)
    return TicketCreateSchema.model_validate(normalized)


def _validation_errors(form_data: dict[str, Any]) -> dict[str, str]:
    """Map schema validation failures into field-specific UI messages."""
    errors: dict[str, str] = {}
    try:
        _build_create_payload(form_data)
    except ValidationError as exc:
        for error in exc.errors():
            location = error.get("loc", ())
            if not location:
                continue
            field_name = str(location[0])
            if field_name == "user_role":
                errors[field_name] = "Select the role that best matches you."
                continue
            errors[field_name] = str(error["msg"])
    return errors


def _guidance_warnings(form_data: dict[str, Any]) -> list[str]:
    """Return non-blocking tips when the request is likely too vague."""
    normalized = _normalized_form_values(form_data)
    title = str(normalized.get("title") or "")
    description = str(normalized.get("description") or "")

    warnings: list[str] = []
    if title and (title.lower() in _GENERIC_TITLES or len(title.split()) < 3):
        warnings.append("Make the title more specific by naming the system, device, or exact error.")
    if description and (len(description) < 60 or len(description.split()) < 12):
        warnings.append("Add more detail to the description, including what you were doing and what you already tried.")
    return warnings


def _format_confirmation_message(ticket_id: int) -> str:
    """Create success message for on submitted."""
    return f"Your request was submitted successfully. Ticket #{ticket_id} is now in the support queue."


def register() -> None:
    """Register the user ticket intake page."""

    @ui.page("/request")
    async def request_page(service: TicketService = Depends(get_ticket_service)):
        logger.info("Rendering request intake page.")

        with frame("Submit Support Ticket"):
            ui.label("Open a support ticket").classes("text-h4 font-bold")
            ui.label(
                "Complete every field with specific details so the support team can route your issue correctly."
            ).classes("text-body1 text-slate-600")

            with ui.row().classes("w-full items-start gap-6"):
                with ui.card().classes("w-full max-w-3xl p-6 gap-4"):
                    with ui.column().classes("w-full gap-4") as form_section:
                        name_input = (
                            ui.input(
                                label="Full name",
                                placeholder="Jane Student",
                                on_change=lambda _: apply_validation_feedback(),
                            )
                            .props("outlined")
                            .classes("w-full")
                        )
                        ui.label(_FIELD_HELPERS["requestor_name"]).classes("text-xs text-slate-500")
                        name_error = ui.label().classes("text-negative text-sm")
                        name_error.set_visibility(False)

                        email_input = (
                            ui.input(
                                label="Email address",
                                placeholder="jane.student@example.edu",
                                on_change=lambda _: apply_validation_feedback(),
                            )
                            .props("outlined type=email")
                            .classes("w-full")
                        )
                        ui.label(_FIELD_HELPERS["requestor_email"]).classes("text-xs text-slate-500")
                        email_error = ui.label().classes("text-negative text-sm")
                        email_error.set_visibility(False)

                        role_input = (
                            ui.select(
                                {role.value: role.value.title() for role in UserRole},
                                label="Role",
                                on_change=lambda _: apply_validation_feedback(),
                            )
                            .props("outlined")
                            .classes("w-full")
                        )
                        ui.label(_FIELD_HELPERS["user_role"]).classes("text-xs text-slate-500")
                        role_error = ui.label().classes("text-negative text-sm")
                        role_error.set_visibility(False)

                        title_input = (
                            ui.input(
                                label="Ticket title",
                                placeholder="Canvas login fails after password reset",
                                on_change=lambda _: apply_validation_feedback(),
                            )
                            .props("outlined")
                            .classes("w-full")
                        )
                        ui.label(_FIELD_HELPERS["title"]).classes("text-xs text-slate-500")
                        title_error = ui.label().classes("text-negative text-sm")
                        title_error.set_visibility(False)

                        description_input = (
                            ui.textarea(
                                label="Description",
                                placeholder="Describe what you were trying to do, what happened, and what you already tried.",
                                on_change=lambda _: apply_validation_feedback(),
                            )
                            .props("outlined autogrow")
                            .classes("w-full")
                        )
                        ui.label(_FIELD_HELPERS["description"]).classes("text-xs text-slate-500")
                        description_error = ui.label().classes("text-negative text-sm")
                        description_error.set_visibility(False)

                        warning_section = ui.column().classes("w-full gap-2")

                        with ui.row().classes("items-center gap-3"):
                            submit_button = ui.button("Submit Ticket")
                            clear_button = ui.button("Clear Form").props("flat")

                    with ui.column().classes("w-full gap-3") as confirmation_section:
                        ui.icon("check_circle", color="positive").classes("text-5xl")
                        ui.label("Request received").classes("text-h5 font-bold text-positive")
                        confirmation_message = ui.label().classes("text-body1")
                        ui.label(
                            "Support can now review your request. Keep an eye on your email for follow up questions."
                        ).classes("text-body2 text-slate-600")
                        submit_another_button = ui.button("Submit Another Ticket")
                    confirmation_section.set_visibility(False)

                with ui.card(align_items="center").classes("w-full max-w-md p-6 gap-3"):
                    with ui.card_section():
                        ui.label("Tips for a faster resolution").classes("text-h6 font-semibold color-red")
                        ui.label("Name the system, app, device, or classroom involved.").classes("text-body2")
                        ui.label("Describe what you expected and what actually happened.").classes("text-body2")
                        ui.label("Include error text, timestamps, or location details when you have them.").classes(
                            "text-body2"
                        )
                    with ui.card_section():
                        ui.label("Mention any steps you already tried, such as restarting or reconnecting.").classes(
                            "text-body2"
                        )

            error_labels = {
                "requestor_name": name_error,
                "requestor_email": email_error,
                "user_role": role_error,
                "title": title_error,
                "description": description_error,
            }

            controls = {
                "requestor_name": name_input,
                "requestor_email": email_input,
                "user_role": role_input,
                "title": title_input,
                "description": description_input,
            }

            def _form_state() -> dict[str, Any]:
                return {name: control.value for name, control in controls.items()}

            def _reset_form() -> None:
                logger.debug("Resetting request intake form state.")
                for field_name, control in controls.items():
                    control.value = _FORM_DEFAULTS[field_name]
                confirmation_section.set_visibility(False)
                form_section.set_visibility(True)
                apply_validation_feedback()

            def apply_validation_feedback() -> dict[str, str]:
                form_state = _form_state()
                errors = _validation_errors(form_state)
                for field_name, label in error_labels.items():
                    message = errors.get(field_name, "")
                    label.set_text(message)
                    label.set_visibility(bool(message))

                warnings = _guidance_warnings(form_state)
                warning_section.clear()
                if warnings:
                    with warning_section:
                        ui.label("Helpful warnings").classes("text-warning text-sm font-medium")
                        for warning in warnings:
                            ui.label(warning).classes("text-warning text-sm")
                warning_section.set_visibility(bool(warnings))

                if errors:
                    submit_button.disable()
                else:
                    submit_button.enable()
                return errors

            async def submit_ticket() -> None:
                errors = apply_validation_feedback()
                if errors:
                    logger.warning("Request intake submission blocked by validation errors: {}", errors)
                    ui.notify("Fix the highlighted fields before submitting.", color="warning")
                    return

                submit_button.disable()
                clear_button.disable()
                logger.info("Submitting user-created support ticket from intake page.")
                try:
                    payload = _build_create_payload(_form_state())
                    created_ticket = await service.create_ticket(payload)
                except ValidationError as exc:
                    logger.warning("Request intake validation failed unexpectedly during submit: {}", exc)
                    apply_validation_feedback()
                    ui.notify("Fix the highlighted fields before submitting.", color="warning")
                    return
                except Exception:
                    logger.exception("Request intake submission failed unexpectedly.")
                    ui.notify("The ticket could not be submitted. Please try again.", color="negative")
                    raise
                finally:
                    clear_button.enable()

                confirmation_message.set_text(_format_confirmation_message(created_ticket.id))
                logger.info("Request intake submission created ticket {}.", created_ticket.id)
                _reset_form()
                form_section.set_visibility(False)
                confirmation_section.set_visibility(True)
                ui.notify("Ticket submitted successfully.", color="positive")

            submit_button.on_click(submit_ticket)
            clear_button.on_click(lambda: _reset_form())
            submit_another_button.on_click(lambda: _reset_form())
            apply_validation_feedback()
