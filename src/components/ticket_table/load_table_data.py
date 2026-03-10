"""Legacy helper for loading mock ticket data from disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger
from src.schemas.service_ticket import ServiceTicketCreate

MOCK_DATA_PATH = Path(__file__).resolve().parents[3] / "data/MOCK_DATA.json"


def load_mock_tickets() -> list[ServiceTicketCreate]:
    """Load mock ticket rows directly from JSON.

    Runtime code now reads ticket rows through the service/repository layer. This
    helper is retained for legacy/test bootstrap workflows only.
    """
    logger.info("Loading mock data from: {}", MOCK_DATA_PATH.as_posix())
    response: list[ServiceTicketCreate] = []
    if not MOCK_DATA_PATH.exists():
        logger.error("LFailed to load mock data from: {}", MOCK_DATA_PATH.as_posix())
        raise RuntimeError(
            f"Mock data directory not found! Checked: {MOCK_DATA_PATH.as_posix()}"
        )
    with open(file=MOCK_DATA_PATH.as_posix(), mode="r", encoding="utf-8") as file:
        raw_data = file.read()
        data: list[dict[str, Any]] = json.loads(raw_data)
        for ticket in data:
            response.append(
                ServiceTicketCreate.model_validate(
                    {
                        key: value
                        for key, value in ticket.items()
                        if key
                        in ServiceTicketCreate.model_fields
                    }
                )
            )
    return response
