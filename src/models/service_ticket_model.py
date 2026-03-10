"""DB Model for Service Ticket"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM as PostgresqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class ServiceUrgency(StrEnum):
    """Service Ticket Urgency"""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ServiceCategory(StrEnum):
    """Service Ticket Urgency"""

    HARDWARE = "Hardware"
    SOFTWARE = "Software"
    NETWORK = "Network"
    SECURITY = "Security"
    OTHER = "Other"


class ServiceTicketModel(Base):
    """ORM model for the service tickets table."""

    __tablename__ = "service_tickets"

    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, autoincrement=True
    )
    urgency: Mapped[ServiceUrgency] = mapped_column(
        PostgresqlEnum(
            ServiceUrgency,
            create_type=True,
            name="service_urgency",
        ),
        nullable=False,
    )
    category: Mapped[ServiceCategory] = mapped_column(
        PostgresqlEnum(
            ServiceCategory,
            create_type=True,
            name="service_category",
        ),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    first_occurrence: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    received_error_message: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    error_message_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignee: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
