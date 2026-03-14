"""Generate deterministic IT helpdesk mock tickets from Kaggle CSV seed intents.

This script preserves the hand-authored demo tickets, derives a stable set of
campus IT support requests from the Kaggle student-query CSV files in
`data/archive/`, validates every payload against `TicketCreateSchema`, and
overwrites `data/MOCK_DATA.json`.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.models import UserRole  # noqa: E402
from src.schemas import TicketCreateSchema  # noqa: E402

ARCHIVE_FILES = (
    REPO_ROOT / "data" / "archive" / "student_query_train.csv",
    REPO_ROOT / "data" / "archive" / "student_query_test.csv",
)
OUTPUT_PATH = REPO_ROOT / "data" / "MOCK_DATA.json"

BASELINE_MANUAL_TICKETS: list[dict[str, str]] = [
    {
        "requestor_name": "Jane Student",
        "requestor_email": "jane.student@example.edu",
        "user_role": "student",
        "title": "Canvas login fails after password reset",
        "description": (
            "I reset my school password this morning and Canvas still says my login is invalid "
            "even though I can sign into some other services."
        ),
    },
    {
        "requestor_name": "Marcus Faculty",
        "requestor_email": "marcus.faculty@example.edu",
        "user_role": "faculty",
        "title": "Cannot connect to campus Wi-Fi in lecture hall",
        "description": (
            "My laptop sees the campus wireless network but authentication keeps failing in the "
            "engineering lecture hall."
        ),
    },
    {
        "requestor_name": "Ava Vendor",
        "requestor_email": "ava.vendor@example.edu",
        "user_role": "vendor",
        "title": "Printer setup package missing on library kiosk",
        "description": (
            "The library kiosk cannot find the print client anymore and users cannot send jobs to the shared printer."
        ),
    },
    {
        "requestor_name": "Noah Alum",
        "requestor_email": "noah.alum@example.edu",
        "user_role": "alum",
        "title": "MFA enrollment keeps looping",
        "description": (
            "The student portal sends me back to the MFA setup screen every time I try to enroll my authenticator app."
        ),
    },
    {
        "requestor_name": "Priya Student",
        "requestor_email": "priya.student@example.edu",
        "user_role": "student",
        "title": "Zoom audio devices not detected in classroom lab",
        "description": (
            "Zoom cannot find a microphone or speakers on the classroom lab machine, and "
            "restarting the app did not help."
        ),
    },
    {
        "requestor_name": "Lena Faculty",
        "requestor_email": "lena.faculty@example.edu",
        "user_role": "faculty",
        "title": "Antivirus warning after installing research tool",
        "description": (
            "After installing a research application, Windows Security flagged the app and I am "
            "not sure whether it is safe to continue."
        ),
    },
]

ROLE_IDENTITIES: dict[UserRole, list[str]] = {
    UserRole.STUDENT: [
        "Avery Student",
        "Jordan Student",
        "Casey Student",
        "Morgan Student",
        "Riley Student",
    ],
    UserRole.FACULTY: [
        "Mina Faculty",
        "Darius Faculty",
        "Sofia Faculty",
        "Elliot Faculty",
        "Harper Faculty",
    ],
    UserRole.ALUM: [
        "Parker Alum",
        "Quinn Alum",
        "Reese Alum",
        "Kendall Alum",
        "Skyler Alum",
    ],
    UserRole.VENDOR: [
        "Rowan Vendor",
        "Sydney Vendor",
        "Taylor Vendor",
        "Blake Vendor",
        "Cameron Vendor",
    ],
    UserRole.OTHER: [
        "Devon Staff",
        "Logan Staff",
        "Emerson Staff",
        "Finley Staff",
        "Sawyer Staff",
    ],
}

ROLE_DOMAINS: dict[UserRole, str] = {
    UserRole.STUDENT: "students.example.edu",
    UserRole.FACULTY: "faculty.example.edu",
    UserRole.ALUM: "alumni.example.edu",
    UserRole.VENDOR: "vendors.example.edu",
    UserRole.OTHER: "staff.example.edu",
}

INTENT_ROLE_CYCLE: dict[str, tuple[UserRole, UserRole]] = {
    "payment_sync": (UserRole.STUDENT, UserRole.OTHER),
    "digital_id": (UserRole.STUDENT, UserRole.VENDOR),
    "event_registration": (UserRole.STUDENT, UserRole.FACULTY),
    "network_access": (UserRole.STUDENT, UserRole.FACULTY),
    "course_registration": (UserRole.STUDENT, UserRole.FACULTY),
    "lms_access": (UserRole.STUDENT, UserRole.STUDENT),
    "records_portal": (UserRole.STUDENT, UserRole.ALUM),
    "profile_access": (UserRole.STUDENT, UserRole.FACULTY),
    "workflow_approval": (UserRole.STUDENT, UserRole.FACULTY),
    "housing_portal": (UserRole.STUDENT, UserRole.OTHER),
    "campus_info": (UserRole.FACULTY, UserRole.VENDOR),
}

LOCATIONS = [
    "engineering building",
    "library commons",
    "north residence hall",
    "student union",
    "science annex",
    "business center",
]
DEVICES = [
    "district Chromebook",
    "Windows 11 laptop",
    "MacBook Air",
    "iPhone",
    "lab workstation",
    "classroom podium PC",
]
ATTEMPTS = [
    "clearing the browser cache",
    "signing out and back in",
    "switching from Chrome to Edge",
    "restarting the device",
    "trying the same step from an incognito window",
]


@dataclass(frozen=True)
class SeedRecord:
    """Single unique Kaggle seed row normalized for generation."""

    query: str
    priority: str
    intent: str
    topic: str
    system_name: str
    deadline_phrase: str | None


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", ".", value.lower()).strip(".")


def _dedupe_key(ticket: dict[str, str]) -> tuple[str, str, str]:
    return (ticket["requestor_email"], ticket["title"], ticket["description"])


def _pick(items: list[str], index: int) -> str:
    return items[index % len(items)]


def _headline(text: str) -> str:
    return text[:1].upper() + text[1:]


def _extract_between(query: str, prefix: str) -> str | None:
    lowered = query.lower()
    if prefix not in lowered:
        return None
    start = lowered.index(prefix) + len(prefix)
    return query[start:].strip(" ?.").strip()


def _extract_deadline_phrase(query: str) -> str | None:
    lowered = query.lower()
    deadline_markers = (
        "today",
        "tomorrow",
        "this friday",
        "next week",
        "in two days",
    )
    for marker in deadline_markers:
        if marker in lowered:
            return marker
    return None


def _normalize_seed(query: str, priority: str) -> SeedRecord:
    lowered = query.lower()

    if "wifi" in lowered:
        return SeedRecord(query, priority, "network_access", "campus Wi-Fi login", "wireless onboarding portal", None)
    if "student id card" in lowered:
        return SeedRecord(query, priority, "digital_id", "student ID pickup pass", "campus card app", None)
    if "sports activities" in lowered:
        return SeedRecord(query, priority, "event_registration", "sports sign-up page", "student life portal", None)
    if "coding club" in lowered:
        return SeedRecord(
            query, priority, "event_registration", "coding club registration", "student life portal", None
        )
    if "cultural fest" in lowered:
        return SeedRecord(
            query, priority, "event_registration", "cultural fest event schedule", "campus events site", None
        )
    if "workshop on ai" in lowered:
        return SeedRecord(query, priority, "event_registration", "AI workshop registration", "campus events site", None)
    if "office hours" in lowered:
        return SeedRecord(query, priority, "campus_info", "faculty office hours", "campus app", None)
    if "cafeteria open on weekends" in lowered:
        return SeedRecord(query, priority, "campus_info", "weekend dining hours", "campus app", None)
    if "library working hours during holidays" in lowered:
        return SeedRecord(query, priority, "campus_info", "holiday library hours", "campus app", None)
    if "seminar hall located" in lowered:
        return SeedRecord(query, priority, "campus_info", "seminar hall map", "wayfinding kiosk", None)
    if "hostel accommodation" in lowered:
        return SeedRecord(query, priority, "housing_portal", "housing request workflow", "housing portal", None)
    if "revaluation of answer sheets" in lowered:
        return SeedRecord(query, priority, "workflow_approval", "revaluation request", "student portal", None)
    if "internship opportunities" in lowered:
        return SeedRecord(query, priority, "campus_info", "internship resources page", "career services portal", None)
    if "midterm exam schedule" in lowered:
        return SeedRecord(query, priority, "campus_info", "midterm exam schedule", "student portal", None)
    if "contact details" in lowered or "bonafide certificate" in lowered:
        topic = "profile update form" if "contact details" in lowered else "document request form"
        return SeedRecord(query, priority, "profile_access", topic, "student portal", None)
    if "syllabus for " in lowered:
        course = _extract_between(query, "syllabus for ") or "course materials"
        return SeedRecord(query, priority, "lms_access", f"{course} materials", "Canvas", None)
    if "attendance details for " in lowered:
        course = _extract_between(query, "attendance details for ") or "class attendance"
        return SeedRecord(query, priority, "records_portal", f"{course} attendance details", "student portal", None)
    if "results for " in lowered:
        period = _extract_between(query, "results for ") or "current term"
        return SeedRecord(query, priority, "records_portal", f"{period} results", "student portal", None)
    if "change my elective subject" in lowered:
        period = _extract_between(query, "change my elective subject for ") or "current term"
        return SeedRecord(
            query, priority, "course_registration", f"elective change for {period}", "student portal", None
        )
    if "register for courses" in lowered:
        return SeedRecord(query, priority, "course_registration", "course registration", "student portal", None)
    if "unable to submit my exam form" in lowered:
        deadline = _extract_deadline_phrase(query)
        return SeedRecord(query, priority, "course_registration", "exam form submission", "student portal", deadline)
    if "cannot access my admit card" in lowered:
        return SeedRecord(query, priority, "records_portal", "admit card download", "student portal", None)
    if "grade sheet" in lowered:
        return SeedRecord(query, priority, "records_portal", "grade sheet correction", "student portal", None)
    if "marked absent in an exam" in lowered:
        return SeedRecord(query, priority, "records_portal", "exam attendance record", "student portal", None)
    if "fee payment" in lowered:
        return SeedRecord(
            query,
            priority,
            "payment_sync",
            "tuition payment sync",
            "billing portal",
            _extract_deadline_phrase(query),
        )
    if "scholarship amount" in lowered:
        period = _extract_between(query, "credited for ") or "the current term"
        return SeedRecord(
            query, priority, "payment_sync", f"scholarship credit status for {period}", "billing portal", None
        )
    if "internship approval" in lowered:
        return SeedRecord(
            query,
            priority,
            "workflow_approval",
            "internship approval workflow",
            "student portal",
            _extract_deadline_phrase(query),
        )
    if "urgent approval for project submission" in lowered:
        return SeedRecord(
            query, priority, "workflow_approval", "project submission approval", "student portal", "today"
        )
    if "enrollment is cancelled" in lowered:
        return SeedRecord(query, priority, "records_portal", "enrollment status correction", "student portal", None)
    return SeedRecord(query, priority, "profile_access", "student portal request", "student portal", None)


def load_seed_rows() -> list[SeedRecord]:
    """Read both CSV files and keep the first occurrence of each unique question."""

    unique_queries: set[str] = set()
    seeds: list[SeedRecord] = []
    for path in ARCHIVE_FILES:
        with path.open(newline="", encoding="utf-8") as file_handle:
            reader = csv.DictReader(file_handle)
            for row in reader:
                query = row["Student_Query"].strip()
                if query in unique_queries:
                    continue
                unique_queries.add(query)
                seeds.append(_normalize_seed(query, row["Priority_Label"].strip()))
    return seeds


def _priority_note(priority: str, deadline_phrase: str | None, variant: int) -> str:
    if priority == "High":
        if deadline_phrase is not None:
            if variant == 0:
                return f"The deadline tied to this task is {deadline_phrase}, so I need it fixed before the workflow closes."
            return (
                f"The deadline is {deadline_phrase}, and at least one other user in my group saw the same behavior "
                "on the same system."
            )
        return "This is blocking a required task today, so I need a fix before I miss the submission window."
    if priority == "Medium":
        if variant == 0:
            return "This is blocking normal work for one user today, but it does not look like a campus-wide outage."
        return "I can continue once this path works again, but right now the system is stopping normal work."
    if variant == 0:
        return "I can work around it for the moment, but I need the correct setup before next week."
    return "This is not urgent, but I would like the system corrected before the next routine use."


def _identity_for(seed: SeedRecord, seed_index: int, variant: int) -> tuple[str, str, str]:
    role = INTENT_ROLE_CYCLE[seed.intent][variant]
    name = _pick(ROLE_IDENTITIES[role], seed_index + (variant * 2))
    email = f"{_slugify(name)}@{ROLE_DOMAINS[role]}"
    return name, email, role.value


def _ticket_payload(
    *,
    requestor_name: str,
    requestor_email: str,
    user_role: str,
    title: str,
    description: str,
) -> dict[str, str]:
    payload = TicketCreateSchema.model_validate(
        {
            "requestor_name": requestor_name,
            "requestor_email": requestor_email,
            "user_role": user_role,
            "title": title,
            "description": description,
        }
    )
    return payload.model_dump(mode="json")


def _build_ticket(seed: SeedRecord, seed_index: int, variant: int) -> dict[str, str]:
    requestor_name, requestor_email, user_role = _identity_for(seed, seed_index, variant)
    location = _pick(LOCATIONS, seed_index + variant)
    device = _pick(DEVICES, seed_index + variant + 1)
    attempt = _pick(ATTEMPTS, seed_index + variant + 2)
    priority_note = _priority_note(seed.priority, seed.deadline_phrase, variant)

    if seed.intent == "payment_sync":
        if variant == 0:
            title = f"{_headline(seed.system_name)} still shows {seed.topic} as pending"
            description = (
                f"The {seed.system_name} still shows {seed.topic} as unpaid even though the transaction already "
                f"cleared. I was trying to complete the payment from my {device} while in the {location}, and the "
                f"account page never refreshed after {attempt}. {priority_note}"
            )
        else:
            title = f"Financial dashboard is missing my updated {seed.topic}"
            description = (
                f"The finance section in the {seed.system_name} never updates the {seed.topic} status after a successful "
                f"payment session. I confirmed the receipt, then tried the same account from a second browser and the "
                f"same stale balance remained. {priority_note}"
            )
    elif seed.intent == "digital_id":
        if variant == 0:
            title = "Campus card app will not load my student ID pickup pass"
            description = (
                f"The {seed.system_name} opens, but the QR pass for my {seed.topic} never loads on my {device}. I signed "
                f"out, signed back in, and the screen stays blank instead of showing the pickup code. {priority_note}"
            )
        else:
            title = "Badge kiosk cannot print my student ID pickup receipt"
            description = (
                f"The self-service badge kiosk in the {location} accepts my lookup, but it never prints the confirmation "
                f"slip tied to my {seed.topic}. A vendor-side restart did not clear the queue, and students are stuck at "
                f"the final print step. {priority_note}"
            )
    elif seed.intent == "event_registration":
        event_topic = seed.topic[:-5] if seed.topic.endswith(" page") else seed.topic
        if variant == 0:
            title = f"{_headline(event_topic)} page will not open in the campus portal"
            description = (
                f"When I open the {seed.topic} area from the {seed.system_name}, the page either spins forever or returns "
                f"me to the home screen. I tried from a {device} in the {location}, and the same broken page loaded after "
                f"{attempt}. {priority_note}"
            )
        else:
            title = f"Registration email never arrived for {event_topic}"
            description = (
                f"I completed the {seed.topic} flow in the {seed.system_name}, but no confirmation email or follow-up link "
                f"ever arrived in my school inbox. I checked spam, retried the form once, and still do not have the "
                f"message that should confirm the registration. {priority_note}"
            )
    elif seed.intent == "network_access":
        if variant == 0:
            title = "Cannot join campus Wi-Fi from my classroom device"
            description = (
                f"My {device} sees the campus network in the {location}, but the {seed.topic} step fails every time I try "
                f"to authenticate. I retried after {attempt}, and the device still drops back to the sign-in prompt. "
                f"{priority_note}"
            )
        else:
            title = "Wireless onboarding portal keeps rejecting campus Wi-Fi login"
            description = (
                f"The {seed.system_name} loads, but after I enter my school credentials it loops back to the start instead "
                f"of completing the {seed.topic}. Another user in the same area saw the same login loop on a second device. "
                f"{priority_note}"
            )
    elif seed.intent == "course_registration":
        if variant == 0:
            title = f"Student portal blocks the {seed.topic} workflow"
            description = (
                f"The {seed.system_name} opens the {seed.topic} page, but it errors out before I can submit the form. I "
                f"tried from a {device} in the {location}, and the same page broke again after {attempt}. {priority_note}"
            )
        else:
            title = f"{_headline(seed.topic)} page times out before submission"
            description = (
                f"I can reach the {seed.topic} section in the {seed.system_name}, but the final submit action hangs until "
                f"the browser times out. I repeated the workflow from two browsers and the timeout happens at the same step. "
                f"{priority_note}"
            )
    elif seed.intent == "lms_access":
        if variant == 0:
            title = f"Canvas is missing {seed.topic}"
            description = (
                f"The {seed.system_name} course shell opens, but the {seed.topic} section is empty even though my classmates "
                f"can see it. I re-synced the course list after {attempt}, and the materials still do not appear. "
                f"{priority_note}"
            )
        else:
            title = f"Chromebook cannot open {seed.topic} in Canvas"
            description = (
                f"My {device} signs into {seed.system_name}, but every link for {seed.topic} fails to load and sends me "
                f"back to the assignment list. I restarted the browser and tried a second network without changing the "
                f"result. {priority_note}"
            )
    elif seed.intent == "records_portal":
        if variant == 0:
            title = f"Student portal shows the wrong status for {seed.topic}"
            description = (
                f"When I open the records section in the {seed.system_name}, the page for {seed.topic} either shows the "
                f"wrong status or never loads its details. I refreshed the portal after {attempt}, and the same incorrect "
                f"state remained. {priority_note}"
            )
        else:
            title = f"Records screen fails before I can review {seed.topic}"
            description = (
                f"I can sign into the {seed.system_name}, but the page for {seed.topic} errors out before I can download or "
                f"verify the record. I tried from a {device} in the {location}, and the failure happens at the same point "
                f"each time. {priority_note}"
            )
    elif seed.intent == "profile_access":
        if variant == 0:
            title = f"{_headline(seed.system_name)} will not save the {seed.topic}"
            description = (
                f"The {seed.system_name} lets me edit the {seed.topic}, but the save action fails and restores the old "
                f"values. I retried after {attempt}, and the portal keeps discarding the updated information. {priority_note}"
            )
        else:
            title = f"MFA prompt loops when I try to open the {seed.topic}"
            description = (
                f"Every time I open the {seed.topic} in the {seed.system_name}, the security prompt sends me back to the "
                f"same verification page instead of letting me continue. I completed the MFA step twice on my {device}, and "
                f"the loop never clears. {priority_note}"
            )
    elif seed.intent == "workflow_approval":
        if variant == 0:
            title = f"{_headline(seed.topic)} is stuck in the portal workflow"
            description = (
                f"The {seed.system_name} still shows {seed.topic} as pending even after the approval step should have moved "
                f"forward. I opened the workflow from the {location}, retried after {attempt}, and the status has not changed. "
                f"{priority_note}"
            )
        else:
            title = f"{_headline(seed.topic)} page crashes before the deadline"
            description = (
                f"I can reach the {seed.topic} step in the {seed.system_name}, but the page crashes when I submit the final "
                f"approval details. The same crash happened on a second browser session from my {device}. {priority_note}"
            )
    elif seed.intent == "housing_portal":
        if variant == 0:
            title = "Housing portal will not submit my room request"
            description = (
                f"The {seed.system_name} accepts every field in the housing request form, but the submit step never finishes. "
                f"I tried from a {device} in the {location}, and the spinner remains on screen after {attempt}. {priority_note}"
            )
        else:
            title = "Campus housing application page keeps spinning forever"
            description = (
                f"When I open the {seed.topic} in the {seed.system_name}, the application page never finishes loading its "
                f"room options. I retried on two networks and the same endless loading state remains. {priority_note}"
            )
    else:
        if variant == 0:
            title = f"Campus app shows the wrong information for {seed.topic}"
            description = (
                f"The {seed.system_name} displays outdated or incomplete details for {seed.topic}, so I cannot trust the "
                f"information it shows. I refreshed the app after {attempt}, and the same stale content remained on my {device}. "
                f"{priority_note}"
            )
        else:
            title = f"Wayfinding kiosk search fails for {seed.topic}"
            description = (
                f"The digital kiosk in the {location} stops responding whenever I search for {seed.topic}. A quick restart "
                f"returns the home screen, but the search function fails again on the next lookup. {priority_note}"
            )

    return _ticket_payload(
        requestor_name=requestor_name,
        requestor_email=requestor_email,
        user_role=user_role,
        title=title,
        description=description,
    )


def build_mock_dataset() -> list[dict[str, str]]:
    """Create the full mock dataset with baseline tickets followed by generated tickets."""

    dataset = [TicketCreateSchema.model_validate(ticket).model_dump(mode="json") for ticket in BASELINE_MANUAL_TICKETS]
    seen = {_dedupe_key(ticket) for ticket in dataset}
    generated_count = 0

    for seed_index, seed in enumerate(load_seed_rows()):
        for variant in (0, 1):
            ticket = _build_ticket(seed, seed_index, variant)
            dedupe_key = _dedupe_key(ticket)
            if dedupe_key in seen:
                raise ValueError(f"Duplicate mock ticket detected for {dedupe_key!r}")
            seen.add(dedupe_key)
            dataset.append(ticket)
            generated_count += 1

    if generated_count < 100:
        raise ValueError(f"Expected at least 100 generated tickets, found {generated_count}.")
    return dataset


def write_mock_dataset(destination: Path = OUTPUT_PATH) -> list[dict[str, str]]:
    """Write the generated dataset to disk and return the payload."""

    dataset = build_mock_dataset()
    destination.write_text(f"{json.dumps(dataset, indent=2)}\n", encoding="utf-8")
    return dataset


def main() -> None:
    dataset = write_mock_dataset()
    generated_count = len(dataset) - len(BASELINE_MANUAL_TICKETS)
    print(f"Wrote {len(dataset)} mock tickets to {OUTPUT_PATH} ({generated_count} generated from Kaggle seeds).")


if __name__ == "__main__":
    main()
