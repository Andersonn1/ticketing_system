"""Tests for custom SQLAlchemy types."""

from __future__ import annotations

import unittest

from src.db.types import Vector


class VectorTypeTests(unittest.TestCase):
    """Verify pgvector bind/result conversion helpers."""

    def test_bind_processor_serializes_python_sequence_to_pgvector_text(self) -> None:
        processor = Vector(3).bind_processor(None)

        self.assertIsNotNone(processor)
        assert processor is not None
        self.assertEqual(processor([1, 2.5, -3]), "[1.00000000,2.50000000,-3.00000000]")

    def test_result_processor_parses_pgvector_text_to_python_list(self) -> None:
        processor = Vector(3).result_processor(None, None)

        self.assertIsNotNone(processor)
        assert processor is not None
        self.assertEqual(processor("[1.00000000,2.50000000,-3.00000000]"), [1.0, 2.5, -3.0])


if __name__ == "__main__":
    unittest.main()
