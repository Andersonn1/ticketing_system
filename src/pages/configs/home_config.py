"""Home Page Configuration"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache


@dataclass(slots=True, frozen=True)
class MonthConfig:
    year: int
    month: int
    max_days: int


@dataclass(frozen=True, slots=True)
class HomeAction:
    """One primary action displayed on the homepage."""

    label: str
    href: str
    icon: str
    primary: bool = False


@dataclass(frozen=True, slots=True)
class HomeFeature:
    """One feature card displayed on the homepage."""

    title: str
    description: str
    icon: str


HOME_ACTIONS: tuple[HomeAction, ...] = (
    HomeAction("Submit Ticket", "/request", "add_circle", primary=True),
    HomeAction("Support Queue", "/manual", "view_list"),
    HomeAction("AI Assist", "/ai-process", "smart_toy"),
    HomeAction("Metrics", "/metrics", "query_stats"),
)

HOME_FEATURES: tuple[HomeFeature, ...] = (
    HomeFeature(
        "Request Intake",
        "Capture support issues through a simple intake flow with clear routing details and user context.",
        "assignment",
    ),
    HomeFeature(
        "Queue Oversight",
        "Review incoming tickets, manage triage decisions, and keep support work moving through one shared queue.",
        "fact_check",
    ),
    HomeFeature(
        "AI-Assisted Handling",
        "Use cloud AI triage to summarize requests, recommend actions, and speed up repetitive service workflows.",
        "auto_awesome",
    ),
)

HOME_STEPS: tuple[str, ...] = (
    "Submit a request with the issue details, affected service, and any troubleshooting already attempted.",
    "Route the request through the support queue so staff can review status, priority, and next actions.",
    "Use AI assistance or manual handling to resolve the issue and respond with clear follow-up guidance.",
)

COMMON_REQUEST_AREAS: tuple[str, ...] = (
    "Account access and password resets",
    "Software installation and application errors",
    "Device, hardware, and peripheral issues",
    "Network, connectivity, and VPN support",
)

SUPPORT_EXPECTATIONS: tuple[str, ...] = (
    "Include exact error text, timestamps, and screenshots when available.",
    "Name the system, device, or workflow affected by the issue.",
    "Note any fixes already attempted so support can avoid repeating steps.",
)


@lru_cache(maxsize=1)
def _get_calendar_month_config() -> MonthConfig:
    """Get the number of days in current month

    Returns:
        int: The number of days in the given month
    """
    current = datetime.now()
    month = current.month
    year = current.year
    # Get the first day of the *next* month
    if month == 12:
        next_month_first_day = date(year + 1, 1, 1)
    else:
        next_month_first_day = date(year, month + 1, 1)

    # Subtract one day to get the last day of the current month
    last_day_of_month = next_month_first_day - timedelta(days=1)

    return MonthConfig(year=year, month=month, max_days=last_day_of_month.day)


@lru_cache(maxsize=1)
def _generate_events() -> list[dict[str, str]]:
    """Generate Random Calendar events for the current month

    Args:
        days (int): Total number of days in the month

    Returns:
        list[dict[str,str]]: The random events for the month
    """

    month_config = _get_calendar_month_config()
    days = [x for x in range(1, month_config.max_days + 1)]

    events = [
        {
            "title": "Closed For Inventory Cataloging",
            "start": "",
            "end": "",
            "color": "red",
        },
        {
            "title": "Launch of New\nStudent Portal",
            "start": "",
            "end": "",
            "color": "green",
        },
        {
            "title": "Teacher Workday",
            "start": "",
            "end": "",
            "color": "blue",
        },
        {
            "title": "Account Audits",
            "start": "",
            "end": "",
            "color": "orange",
        },
    ]
    event_days = random.sample(days, k=len(events))
    hours = [x for x in range(5, 21)]
    mins = [x for x in range(1, 60)]
    span = [x for x in range(1, 5)]
    for event in events:
        day_to_remove = random.choice(event_days)
        day = day_to_remove
        hour = random.choice(hours)
        minute = random.choice(mins)
        event["start"] = datetime(
            year=month_config.year, month=month_config.month, day=day, hour=hour, minute=minute, second=0
        ).strftime(r"%Y-%m-%d %H:%M:%S")
        end_hour = random.choice(span)
        hour = hour if end_hour > 20 else end_hour
        all_day = "closed" in event["title"].lower()
        day = day + 1 if all_day and day + 1 < month_config.max_days else day
        minute = 0 if all_day else minute
        event["end"] = datetime(
            year=month_config.year, month=month_config.month, day=day, hour=hour, minute=minute, second=0
        ).strftime(r"%Y-%m-%d %H:%M:%S")
        event_days.remove(day_to_remove)
    return events


_CALENDAR_OPTIONS = {
    "initialView": "dayGridMonth",
    "headerToolbar": {"left": "title", "right": ""},
    "slotMinTime": "05:00:00",
    "slotMaxTime": "20:00:00",
    "allDaySlot": True,
    "timeZone": "local",
    "height": "auto",
    "width": "auto",
    "events": _generate_events(),
}
_HEADER_SCRIPT_TAG = """
    <script src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.20/index.global.min.js'></script>
    <script>
      document.addEventListener('DOMContentLoaded', function() {
        let calendarEl = document.getElementById('calendar');
        let calendar = new FullCalendar.Calendar(calendarEl,CALENDAR_OPTIONS);
        calendar.render();
      });
    </script>
"""

HEADER_SCRIPT_TAG = _HEADER_SCRIPT_TAG.replace("CALENDAR_OPTIONS", json.dumps(_CALENDAR_OPTIONS))
