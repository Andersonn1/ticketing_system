"""Canonical ticket model and enums."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import TIMESTAMP, BigInteger, Enum, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class UserRole(StrEnum):
    """Supported requestor roles."""

    STUDENT = "student"
    FACULTY = "faculty"
    ALUM = "alum"
    VENDOR = "vendor"
    OTHER = "other"


class ServicePriority(StrEnum):
    """Priority assigned to a ticket."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AIConfidence(StrEnum):
    """Confidence assigned to the AI triage output."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ServiceCategory(StrEnum):
    """High-level ticket category."""

    HARDWARE = "hardware"
    SOFTWARE = "software"
    NETWORK = "network"
    SECURITY = "security"
    OTHER = "other"


class ServiceStatus(StrEnum):
    """Ticket lifecycle state."""

    OPEN = "open"
    PENDING = "pending"
    CLOSED = "closed"


class TicketModel(Base):
    """Primary application ticket record."""

    __tablename__ = "ticket"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False, autoincrement=True)
    requestor_name: Mapped[str] = mapped_column(String(length=250), nullable=False)
    requestor_email: Mapped[str] = mapped_column(String(length=275), nullable=False)
    user_role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=False),
        nullable=False,
        server_default=text("'OTHER'"),
    )
    title: Mapped[str] = mapped_column(String(length=125), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ServiceStatus] = mapped_column(
        Enum(ServiceStatus, name="service_status", create_constraint=False),
        nullable=False,
        server_default=text("'OPEN'"),
    )
    priority: Mapped[ServicePriority] = mapped_column(
        Enum(ServicePriority, name="service_priority", create_constraint=False),
        nullable=False,
        server_default=text("'LOW'"),
    )
    category: Mapped[ServiceCategory] = mapped_column(
        Enum(ServiceCategory, name="service_category", create_constraint=False),
        nullable=False,
        server_default=text("'OTHER'"),
    )
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_next_steps: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    manual_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    manual_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    manual_next_steps: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    ai_confidence: Mapped[AIConfidence | None] = mapped_column(
        Enum(AIConfidence, name="ai_confidence", create_constraint=False),
        nullable=True,
    )
    ai_trace: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True, server_default=None)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
