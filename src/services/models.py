"""Service Models"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SeedSummary:
    """Summary of seed/upsert counts."""

    created: int
    updated: int
    skipped: int


@dataclass(slots=True)
class TicketSeedResult:
    """Startup seed report for tickets and KB chunks."""

    summary: SeedSummary
    payloads_processed: int
    kb_chunks_upserted: int


@dataclass(slots=True)
class TriageBatchResult:
    """Batch triage outcome for the AI page."""

    completed: list[int]
    failed: dict[int, str]
