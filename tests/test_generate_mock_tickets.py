"""Tests for deterministic mock-ticket generation from Kaggle CSV seeds."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.generate_mock_tickets import (
    BASELINE_MANUAL_TICKETS,
    OUTPUT_PATH,
    build_mock_dataset,
    load_seed_rows,
)
from src.schemas import TicketCreateSchema


def _business_key(ticket: dict[str, str]) -> tuple[str, str, str]:
    return (ticket["requestor_email"], ticket["title"], ticket["description"])


class GenerateMockTicketsTests(unittest.TestCase):
    """Verify the CSV-driven mock dataset generator."""

    def test_seed_rows_are_deduped(self) -> None:
        seeds = load_seed_rows()

        self.assertEqual(len(seeds), 57)
        self.assertEqual(
            seeds[0].query,
            "My fee payment is not reflecting and the last date is in two days.",
        )
        self.assertEqual(seeds[-1].query, "I am unable to submit my exam form and the deadline is today.")

    def test_generated_dataset_is_valid_and_unique(self) -> None:
        dataset = build_mock_dataset()
        generated_only = dataset[len(BASELINE_MANUAL_TICKETS) :]

        self.assertGreaterEqual(len(generated_only), 100)
        self.assertGreaterEqual(len(dataset), len(BASELINE_MANUAL_TICKETS) + 100)

        validated = [TicketCreateSchema.model_validate(ticket).model_dump(mode="json") for ticket in dataset]
        self.assertEqual(validated, dataset)
        self.assertEqual(len({_business_key(ticket) for ticket in dataset}), len(dataset))

    def test_generation_is_deterministic_for_first_generated_rows(self) -> None:
        dataset = build_mock_dataset()
        generated_only = dataset[len(BASELINE_MANUAL_TICKETS) :]

        self.assertEqual(
            generated_only[:3],
            [
                {
                    "requestor_name": "Avery Student",
                    "requestor_email": "avery.student@students.example.edu",
                    "user_role": "student",
                    "title": "Billing portal still shows tuition payment sync as pending",
                    "description": (
                        "The billing portal still shows tuition payment sync as unpaid even though the transaction "
                        "already cleared. I was trying to complete the payment from my Windows 11 laptop while in "
                        "the engineering building, and the account page never refreshed after switching from Chrome "
                        "to Edge. The deadline tied to this task is in two days, so I need it fixed before the "
                        "workflow closes."
                    ),
                },
                {
                    "requestor_name": "Emerson Staff",
                    "requestor_email": "emerson.staff@staff.example.edu",
                    "user_role": "other",
                    "title": "Financial dashboard is missing my updated tuition payment sync",
                    "description": (
                        "The finance section in the billing portal never updates the tuition payment sync status after "
                        "a successful payment session. I confirmed the receipt, then tried the same account from a "
                        "second browser and the same stale balance remained. The deadline is in two days, and at least "
                        "one other user in my group saw the same behavior on the same system."
                    ),
                },
                {
                    "requestor_name": "Jordan Student",
                    "requestor_email": "jordan.student@students.example.edu",
                    "user_role": "student",
                    "title": "Campus card app will not load my student ID pickup pass",
                    "description": (
                        "The campus card app opens, but the QR pass for my student ID pickup pass never loads on my "
                        "MacBook Air. I signed out, signed back in, and the screen stays blank instead of showing the "
                        "pickup code. I can work around it for the moment, but I need the correct setup before next week."
                    ),
                },
            ],
        )

    def test_mock_data_file_matches_generated_dataset(self) -> None:
        expected = build_mock_dataset()
        actual = json.loads(Path(OUTPUT_PATH).read_text(encoding="utf-8"))

        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
