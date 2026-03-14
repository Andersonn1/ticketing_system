"""Startup seed helpers for tickets and KB docs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from loguru import logger

from src.dependencies import get_ticket_service
from src.schemas import TicketCreateSchema
from src.services import TicketSeedResult

MOCK_DATA_PATH = Path(__file__).resolve().parents[2] / "data/MOCK_DATA.json"


@dataclass(slots=True)
class KBDoc:
    """Static KB document used for demo retrieval."""

    source_name: str
    chunk_text: str
    metadata: dict[str, str]


KB_DOCS: Final[list[KBDoc]] = [
    KBDoc(
        source_name="password_reset_policy",
        chunk_text="If a student resets their password, access to Canvas and email may take up to 15 minutes to sync. Ask the student to wait 15 minutes, clear browser cache, and try again.",
        metadata={"category": "password_reset"},
    ),
    KBDoc(
        source_name="wifi_troubleshooting",
        chunk_text="For campus Wi-Fi issues, confirm the user is on the correct SSID, forget the network, reconnect, and re-enter credentials. If still failing, check whether the account is locked.",
        metadata={"category": "network"},
    ),
    KBDoc(
        source_name="printer_setup_library",
        chunk_text="Library printers require the school print client. Install the printer package, restart the device, and ensure the user is on campus network or VPN.",
        metadata={"category": "printer_issue"},
    ),
    KBDoc(
        source_name="mfa_enrollment",
        chunk_text="If MFA setup fails, confirm device time is synced, remove stale authenticator entries, and retry enrollment from the student portal.",
        metadata={"category": "security_concern"},
    ),
]


def load_mock_tickets(path: Path = MOCK_DATA_PATH) -> list[TicketCreateSchema]:
    """Load canonical ticket seed data from disk."""
    logger.info("Loading mock data from {}", path.as_posix())
    if not path.exists():
        raise RuntimeError(f"Mock data file not found: {path.as_posix()}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    return [TicketCreateSchema.model_validate(ticket) for ticket in raw]


async def run_seed(path: Path = MOCK_DATA_PATH) -> TicketSeedResult:
    """Seed tickets and KB docs through the async service layer."""
    service = get_ticket_service()
    ticket_payloads = load_mock_tickets(path)
    summary = await service.seed_tickets(ticket_payloads)
    kb_chunks_upserted = await service.seed_kb_docs(
        [
            {
                "source_name": doc.source_name,
                "chunk_text": doc.chunk_text,
                "metadata": doc.metadata,
            }
            for doc in KB_DOCS
        ]
    )
    ticket_embeddings_upserted = await service.refresh_ticket_embeddings()
    return TicketSeedResult(
        summary=summary,
        payloads_processed=len(ticket_payloads),
        kb_chunks_upserted=kb_chunks_upserted,
        ticket_embeddings_upserted=ticket_embeddings_upserted,
    )
