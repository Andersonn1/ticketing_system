"""Data model package."""

from __future__ import annotations

from .embedding import TicketEmbeddingModel
from .kb_chunk import KBChunkModel
from .ticket import (
    AIConfidence,
    ServiceCategory,
    ServiceDepartment,
    ServicePriority,
    ServiceStatus,
    TicketModel,
    UserRole,
)

__all__ = [
    "AIConfidence",
    "ServiceCategory",
    "ServiceDepartment",
    "ServicePriority",
    "ServiceStatus",
    "TicketEmbeddingModel",
    "KBChunkModel",
    "TicketModel",
    "UserRole",
]
