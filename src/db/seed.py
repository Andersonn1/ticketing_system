"""Seed the service_tickets table from MOCK_DATA.json."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeAlias

from loguru import logger

from src.schemas.service_ticket import ServiceTicketCreate
from src.services.service_ticket_service import SeedSummary, ServiceTicketService

MOCK_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "MOCK_DATA.json"

AllowedPayload: TypeAlias = dict[str, Any]


@dataclass(frozen=True)
class SeedResult:
    """Seed execution summary."""

    summary: SeedSummary
    payloads_processed: int


async def load_payloads(mock_data_path: Path) -> list[ServiceTicketCreate]:
    """Load service tickets from mock file and ignore DB-owned identifiers."""
    logger.info("Loading mock payloads from: {}", mock_data_path.as_posix())
    raw_json = mock_data_path.read_text(encoding="utf-8")
    payloads: list[AllowedPayload] = json.loads(raw_json)

    if not isinstance(payloads, list):
        raise ValueError(f"Expected a JSON list in {mock_data_path.as_posix()}")

    records: list[ServiceTicketCreate] = []
    for raw_payload in payloads:
        if not isinstance(raw_payload, dict):
            raise TypeError(f"Expected object entries in {mock_data_path.as_posix()}")

        normalized: AllowedPayload = {
            key: value
            for key, value in raw_payload.items()
            if key in ServiceTicketCreate.model_fields
        }
        if "id" in raw_payload:
            logger.debug("Ignoring id from mock payload: {}", raw_payload.get("id"))

        records.append(ServiceTicketCreate.model_validate(normalized))

    return records


async def run_seed(mock_data_path: Path) -> SeedResult:
    """Run idempotent seed/upsert against PostgreSQL."""
    payloads = await load_payloads(mock_data_path)
    summary = await ServiceTicketService().seed_tickets(payloads)
    return SeedResult(summary=summary, payloads_processed=len(payloads))


async def main() -> int:
    """CLI entrypoint for seed script."""
    parser = argparse.ArgumentParser(description="Seed service_tickets from JSON.")
    parser.add_argument(
        "--path",
        default=str(MOCK_DATA_PATH),
        help="Path to the mock data json payload.",
    )
    parser.add_argument(
        "--path-only",
        action="store_true",
        help="Validate payload path only; no DB write.",
    )
    args = parser.parse_args()

    data_path = Path(args.path)
    payloads = await load_payloads(data_path)
    if args.path_only:
        print(f"{len(payloads)} ticket payload(s) parsed from {data_path}")
        return 0

    summary = await ServiceTicketService().seed_tickets(payloads)
    result = SeedResult(summary=summary, payloads_processed=len(payloads))
    print(
        "Seed complete: "
        f"{result.summary.created} created, "
        f"{result.summary.updated} updated, "
        f"{result.summary.skipped} skipped "
        f"from {result.payloads_processed} payload(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
