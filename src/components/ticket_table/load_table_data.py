"""Load Mock Data"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger

from src.schemas.service_ticket import ServiceTicket

MOCK_DATA_PATH = Path(__file__).parents[3] / "data/MOCK_DATA.json"


def load_mock_tickets() -> list[ServiceTicket]:
    logger.info("Loading mock data from: {}", MOCK_DATA_PATH.as_posix())
    response = []
    if not MOCK_DATA_PATH.exists():
        logger.error("LFailed to load mock data from: {}", MOCK_DATA_PATH.as_posix())
        raise RuntimeError(
            f"Mock data directory not found! Checked: {MOCK_DATA_PATH.as_posix()}"
        )
    with open(file=MOCK_DATA_PATH.as_posix(), mode="r", encoding="utf-8") as file:
        raw_data = file.read()
        data: list[dict[str, Any]] = json.loads(raw_data)
        for ticket in data:
            response.append(ServiceTicket(**ticket))
    return response
