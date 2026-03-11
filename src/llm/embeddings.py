"""Embeddings Helper"""

from __future__ import annotations


def to_pgvector_str(values: list[float]) -> str:
    """Convert list of floats to postgres vector string"""
    return "[" + ",".join(f"{v:.8f}" for v in values) + "]"
