"""Ticket embedding model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, BigInteger, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base
from src.db.types import Vector

if TYPE_CHECKING:
    from src.models.ticket import TicketModel


class TicketEmbeddingModel(Base):
    """Embedding row used for similar-ticket retrieval."""

    __tablename__ = "ticket_embedding"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False, autoincrement=True, unique=True)
    ticket_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ticket.id", ondelete="CASCADE"), nullable=False)
    combined_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    ticket: Mapped["TicketModel"] = relationship("TicketModel", uselist=False, lazy="selectin")
