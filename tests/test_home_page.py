"""Homepage and navigation content tests."""

from __future__ import annotations

import unittest

from src.core.header_menu import NAV_LINKS
from src.pages.home_page import COMMON_REQUEST_AREAS, HOME_ACTIONS, HOME_FEATURES, HOME_STEPS, SUPPORT_EXPECTATIONS


class HomePageContentTests(unittest.TestCase):
    """Verify homepage content stays aligned with the generic helpdesk experience."""

    def test_home_actions_keep_expected_order_and_routes(self) -> None:
        self.assertEqual(
            [(action.label, action.href, action.primary) for action in HOME_ACTIONS],
            [
                ("Submit Ticket", "/request", True),
                ("Support Queue", "/manual", False),
                ("AI Assist", "/ai-process", False),
            ],
        )

    def test_navigation_labels_match_homepage_entry_points(self) -> None:
        self.assertEqual(
            NAV_LINKS,
            (
                ("Home", "/"),
                ("Submit Ticket", "/request"),
                ("Support Queue", "/manual"),
                ("AI Assist", "/ai-process"),
            ),
        )

    def test_homepage_support_cards_cover_intake_queue_and_ai_assist(self) -> None:
        self.assertEqual(
            [feature.title for feature in HOME_FEATURES],
            ["Request Intake", "Queue Oversight", "AI-Assisted Handling"],
        )

    def test_support_flow_and_sidebar_content_remain_complete(self) -> None:
        self.assertEqual(len(HOME_STEPS), 3)
        self.assertEqual(len(COMMON_REQUEST_AREAS), 4)
        self.assertEqual(len(SUPPORT_EXPECTATIONS), 3)


if __name__ == "__main__":
    unittest.main()
