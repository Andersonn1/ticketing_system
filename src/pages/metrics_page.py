"""Application Metrics Page"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from statistics import median

from fastapi import Depends
from loguru import logger
from nicegui import ui

from src.core.theme import frame
from src.dependencies import get_ticket_service
from src.schemas import TicketResponseSchema
from src.services import TicketService


@dataclass(frozen=True, slots=True)
class MetricsSummary:
    """Aggregate metrics derived from ticket records."""

    total_tickets: int
    ai_triaged_tickets: int
    manual_triaged_tickets: int
    review_needed_tickets: int
    missing_information_tickets: int
    median_ai_processing_ms: int | None
    average_ai_processing_ms: int | None
    average_top_kb_similarity: float | None
    average_top_ticket_similarity: float | None
    status_counts: list[tuple[str, int]]
    priority_counts: list[tuple[str, int]]
    category_counts: list[tuple[str, int]]
    department_counts: list[tuple[str, int]]
    confidence_counts: list[tuple[str, int]]
    review_rows: list[dict[str, str | int | None]]


def _has_ai_triage(ticket: TicketResponseSchema) -> bool:
    """Return whether a ticket has persisted AI triage content."""
    return any(
        [
            bool(ticket.ai_summary),
            bool(ticket.ai_recommended_action),
            bool(ticket.ai_reasoning),
            bool(ticket.ai_confidence),
            bool(ticket.department),
        ]
    )


def _has_manual_triage(ticket: TicketResponseSchema) -> bool:
    """Return whether a ticket has persisted manual triage content."""
    return any(
        [
            bool(ticket.manual_summary),
            bool(ticket.manual_response),
            bool(ticket.manual_next_steps),
        ]
    )


def _needs_review(ticket: TicketResponseSchema) -> bool:
    """Return whether a ticket should be reviewed by staff."""
    if not _has_ai_triage(ticket):
        return False
    missing_information = (ticket.ai_missing_information or "").strip().lower()
    return bool(
        ticket.ai_confidence is not None
        and ticket.ai_confidence.value == "low"
        or (missing_information and missing_information != "none")
    )


def _average(values: list[float]) -> float | None:
    """Return the arithmetic mean of a list or None when empty."""
    if not values:
        return None
    return sum(values) / len(values)


def _sorted_counts(counter: Counter[str]) -> list[tuple[str, int]]:
    """Return counts sorted by descending frequency then label."""
    return sorted(counter.items(), key=lambda item: (-item[1], item[0]))


def _build_metrics_summary(tickets: list[TicketResponseSchema]) -> MetricsSummary:
    """Build the application metrics snapshot from ticket records."""
    status_counts: Counter[str] = Counter()
    priority_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    department_counts: Counter[str] = Counter()
    confidence_counts: Counter[str] = Counter()
    processing_times: list[int] = []
    kb_similarities: list[float] = []
    ticket_similarities: list[float] = []
    review_rows: list[dict[str, str | int | None]] = []

    ai_triaged_tickets = 0
    manual_triaged_tickets = 0
    review_needed_tickets = 0
    missing_information_tickets = 0

    for ticket in tickets:
        status_counts[ticket.status.value.title()] += 1
        priority_counts[ticket.priority.value.title()] += 1
        category_counts[ticket.category.value.replace("_", " ").title()] += 1

        if ticket.department is not None:
            department_counts[ticket.department.value.replace("_", " ").title()] += 1
        if ticket.ai_confidence is not None:
            confidence_counts[ticket.ai_confidence.value.title()] += 1

        if _has_ai_triage(ticket):
            ai_triaged_tickets += 1
        if _has_manual_triage(ticket):
            manual_triaged_tickets += 1
        if ticket.ai_processing_ms is not None:
            processing_times.append(ticket.ai_processing_ms)

        missing_information = (ticket.ai_missing_information or "").strip()
        if missing_information and missing_information.lower() != "none":
            missing_information_tickets += 1

        if ticket.ai_trace is not None:
            if ticket.ai_trace.kb_matches:
                kb_similarities.append(float(ticket.ai_trace.kb_matches[0].similarity))
            if ticket.ai_trace.ticket_matches:
                ticket_similarities.append(float(ticket.ai_trace.ticket_matches[0].similarity))

        if _needs_review(ticket):
            review_needed_tickets += 1
            review_rows.append(
                {
                    "id": ticket.id,
                    "title": ticket.title,
                    "confidence": ticket.ai_confidence.value.title() if ticket.ai_confidence else None,
                    "missing_information": ticket.ai_missing_information,
                    "department": ticket.department.value.replace("_", " ").title() if ticket.department else None,
                }
            )

    median_processing_ms = int(median(processing_times)) if processing_times else None
    average_processing_ms = (
        int(_average([float(value) for value in processing_times]) or 0) if processing_times else None
    )

    return MetricsSummary(
        total_tickets=len(tickets),
        ai_triaged_tickets=ai_triaged_tickets,
        manual_triaged_tickets=manual_triaged_tickets,
        review_needed_tickets=review_needed_tickets,
        missing_information_tickets=missing_information_tickets,
        median_ai_processing_ms=median_processing_ms,
        average_ai_processing_ms=average_processing_ms,
        average_top_kb_similarity=_average(kb_similarities),
        average_top_ticket_similarity=_average(ticket_similarities),
        status_counts=_sorted_counts(status_counts),
        priority_counts=_sorted_counts(priority_counts),
        category_counts=_sorted_counts(category_counts),
        department_counts=_sorted_counts(department_counts),
        confidence_counts=_sorted_counts(confidence_counts),
        review_rows=sorted(review_rows, key=lambda x: int(x["id"] or 0)),
    )


def _format_processing_ms(value: int | None) -> str:
    """Format milliseconds as a readable seconds string."""
    if value is None:
        return "N/A"
    return f"{value / 1000:.2f}s"


def _format_similarity(value: float | None) -> str:
    """Format similarity score as a three-decimal string."""
    if value is None:
        return "N/A"
    return f"{value:.3f}"


def _render_stat_card(title: str, value: str, caption: str) -> None:
    """Render one compact summary card."""
    with ui.card().classes("col flex-1 min-w-[210px] p-5 gap-2 bg-slate-50"):
        ui.label(title).classes("text-body2 text-slate-600 uppercase tracking-wide")
        ui.label(value).classes("text-h4 font-bold text-primary")
        ui.label(caption).classes("text-body2 text-slate-600")


def _render_distribution_card(title: str, rows: list[tuple[str, int]], empty_message: str) -> None:
    """Render one distribution table."""
    with ui.card().classes("col flex-1 min-w-[260px] p-5 gap-3"):
        ui.label(title).classes("text-h6 font-semibold")
        if not rows:
            ui.label(empty_message).classes("text-body2 text-slate-500")
            return
        for label, count in rows:
            with ui.row().classes("w-full items-center justify-between gap-3"):
                ui.label(label).classes("text-body2 text-slate-700")
                ui.badge(str(count)).props("color=primary")


def _render_review_table(rows: list[dict[str, str | int | None]]) -> None:
    """Render tickets flagged for human review."""
    with ui.card().classes("w-full p-5 gap-4"):
        ui.label("Tickets Needing Review").classes("text-h6 font-semibold")
        if not rows:
            ui.label("No tickets are currently flagged by AI confidence or missing-information rules.").classes(
                "text-body2 text-slate-500"
            )
            return
        ui.table(
            columns=[
                {"name": "id", "label": "Ticket", "field": "id", "align": "left"},
                {"name": "title", "label": "Title", "field": "title", "align": "left"},
                {"name": "confidence", "label": "Confidence", "field": "confidence", "align": "left"},
                {
                    "name": "department",
                    "label": "Department",
                    "field": "department",
                    "align": "left",
                },
                {
                    "name": "missing_information",
                    "label": "Missing Information",
                    "field": "missing_information",
                    "align": "left",
                },
            ],
            rows=rows,
            row_key="id",
            pagination=8,
        ).classes("w-full")


def _render_metrics(summary: MetricsSummary) -> None:
    """Render the metrics dashboard content."""
    with ui.column().classes("w-full max-w-7xl mx-auto gap-6 px-4 py-6 md:px-8"):
        ui.label("AI Metrics").classes("text-h4 font-bold")
        ui.label(
            "Track AI triage volume, routing behavior, review risk, and retrieval quality from persisted ticket data."
        ).classes("text-body1 text-slate-600 max-w-4xl")

        with ui.row().classes("w-full gap-4 items-stretch"):
            _render_stat_card("Total Tickets", str(summary.total_tickets), "All tickets currently stored in the app.")
            _render_stat_card(
                "AI Triaged",
                str(summary.ai_triaged_tickets),
                "Tickets with persisted OpenAI triage output.",
            )
            _render_stat_card(
                "Median AI Time",
                _format_processing_ms(summary.median_ai_processing_ms),
                "Median end-to-end AI triage duration.",
            )
            _render_stat_card(
                "Review Needed",
                str(summary.review_needed_tickets),
                "Low-confidence or missing-information tickets.",
            )

        with ui.row().classes("w-full gap-4 items-stretch"):
            _render_stat_card(
                "Manual Triaged",
                str(summary.manual_triaged_tickets),
                "Tickets with a saved human triage record.",
            )
            _render_stat_card(
                "Avg AI Time",
                _format_processing_ms(summary.average_ai_processing_ms),
                "Average end-to-end AI triage duration.",
            )
            _render_stat_card(
                "Missing Info",
                str(summary.missing_information_tickets),
                "Tickets where AI reported missing information.",
            )
            _render_stat_card(
                "Top KB Similarity",
                _format_similarity(summary.average_top_kb_similarity),
                "Average similarity of the top retrieved KB match.",
            )

        with ui.card().classes("w-full p-5 gap-4 bg-slate-50"):
            ui.label("Retrieval Health").classes("text-h6 font-semibold")
            with ui.row().classes("w-full gap-6 items-center"):
                ui.label(
                    f"Average top similar-ticket score: {_format_similarity(summary.average_top_ticket_similarity)}"
                ).classes("text-body1")
                ui.label(
                    "Higher similarity usually means the retrieval layer is finding stronger prior examples."
                ).classes("text-body2 text-slate-600")

        with ui.row().classes("w-full gap-4 items-stretch"):
            _render_distribution_card("Workflow Status", summary.status_counts, "No tickets available.")
            _render_distribution_card("Priority Mix", summary.priority_counts, "No priorities available.")
            _render_distribution_card("AI Confidence", summary.confidence_counts, "No AI confidence data yet.")

        with ui.row().classes("w-full gap-4 items-stretch"):
            _render_distribution_card("Category Routing", summary.category_counts, "No categories available.")
            _render_distribution_card("Department Routing", summary.department_counts, "No departments assigned yet.")

        _render_review_table(summary.review_rows)


def register() -> None:
    """Register the metrics page."""

    @ui.page("/metrics")
    async def metrics_page(service: TicketService = Depends(get_ticket_service)):
        logger.info("Rendering metrics page.")
        with frame("Metrics"):
            content = ui.column().classes("w-full")

            async def refresh_metrics() -> None:
                tickets = await service.list_tickets()
                logger.info("Metrics page loaded {} tickets.", len(tickets))
                summary = _build_metrics_summary(tickets)
                content.clear()
                with content:
                    _render_metrics(summary)

            with ui.row().classes("w-full justify-end px-4 pt-4 md:px-8"):
                ui.button("Refresh Metrics", on_click=refresh_metrics).props("outline color=primary")

            await refresh_metrics()
