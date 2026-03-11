"""Data repositories."""

from .kb_chunk_repository import KBChunkRepository
from .ticket_embedding_repository import TicketEmbeddingRepository
from .ticket_repository import TicketRepository

__all__ = [
    "KBChunkRepository",
    "TicketRepository",
    "TicketEmbeddingRepository",
]
