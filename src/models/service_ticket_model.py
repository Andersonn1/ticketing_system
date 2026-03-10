"""DB Model for Service Ticket"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Enum, String, Text
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

    id: Mapped[int] = mapped_column(primary_key=True)
    urgency: Mapped[ServiceUrgency] = mapped_column(
        Enum(ServiceUrgency, validate_strings=True, native_enum=False),
        nullable=False,
    )
    category: Mapped[ServiceCategory] = mapped_column(
        Enum(ServiceCategory, validate_strings=True, native_enum=False),
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
