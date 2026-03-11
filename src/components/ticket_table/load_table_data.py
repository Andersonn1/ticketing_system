"""Legacy helper for loading mock ticket data from disk."""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

from loguru import logger

from src.schemas.schema import TicketCreateSchema

MOCK_DATA_PATH = Path(__file__).resolve().parents[3] / "data/MOCK_DATA.json"


@warnings.deprecated("This method has been replaced and needs to be removed after refactor complete")
def load_mock_tickets() -> list[TicketCreateSchema]:
    """Load mock ticket rows directly from JSON.

    Code now reads ticket rows through the service/repository layer.
    Keeping this helper for legacy/test bootstrap workflows only.
    """
    logger.info("Loading mock data from: {}", MOCK_DATA_PATH.as_posix())
    response: list[TicketCreateSchema] = []
    if not MOCK_DATA_PATH.exists():
        logger.error("LFailed to load mock data from: {}", MOCK_DATA_PATH.as_posix())
        raise RuntimeError(f"Mock data directory not found! Checked: {MOCK_DATA_PATH.as_posix()}")
    with open(file=MOCK_DATA_PATH.as_posix(), mode="r", encoding="utf-8") as file:
        raw_data = file.read()
        data: list[dict[str, Any]] = json.loads(raw_data)
        for ticket in data:
            response.append(
                TicketCreateSchema.model_validate(
                    {key: value for key, value in ticket.items() if key in TicketCreateSchema.model_fields}
                )
            )
    return response
