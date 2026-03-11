"""Application schemas for tickets and AI triage."""

from __future__ import annotations

from datetime import datetime

from pydantic import EmailStr, Field, field_serializer, field_validator

from src.models import (
    AIConfidence,
    ServiceCategory,
    ServicePriority,
    ServiceStatus,
    UserRole,
)
from src.schemas.base import BaseSchema


class TicketCreateSchema(BaseSchema):
    """Payload required to create a ticket."""

    requestor_name: str = Field(..., description="The name of the person who made the request")
    requestor_email: EmailStr = Field(..., description="The email of the person who made the request")
    user_role: UserRole = Field(..., description="The role of the person who made the request")
    title: str = Field(..., description="The title assigned to the ticket")
    description: str = Field(..., description="A brief description of the issue")

    @field_validator("requestor_name", "requestor_email", "title", "description", mode="before")
    @classmethod
    def strip_text_fields(cls, value: object) -> object:
        """Trim user-entered string fields before validating them."""
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("requestor_name")
    @classmethod
    def validate_requestor_name(cls, value: str) -> str:
        if not value:
            raise ValueError("Enter your name.")
        if not 2 <= len(value) <= 250:
            raise ValueError("Name must be between 2 and 250 characters.")
        return value

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        if not value:
            raise ValueError("Enter a ticket title.")
        if not 8 <= len(value) <= 125:
            raise ValueError("Title must be between 8 and 125 characters.")
        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        if not value:
            raise ValueError("Enter a description of the issue.")
        if not 20 <= len(value) <= 4000:
            raise ValueError("Description must be between 20 and 4000 characters.")
        return value


class ManualTriageSchema(BaseSchema):
    """Payload required for helpdesk workers to manually triage a ticket."""

    summary: str = Field(..., description="The human-authored summary of the issue")
    response: str = Field(..., description="The response the helpdesk worker will send")
    next_steps: list[str] = Field(default_factory=list, description="Human-authored next steps")
    priority: ServicePriority = Field(..., description="The priority assigned by the helpdesk worker")
    category: ServiceCategory = Field(..., description="The category assigned by the helpdesk worker")
    status: ServiceStatus = Field(..., description="The manual triage workflow status")

    @field_validator("summary", "response", mode="before")
    @classmethod
    def strip_text_fields(cls, value: object) -> object:
        """Trim user-entered string fields before validating them."""
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        if not value:
            raise ValueError("Enter a triage summary.")
        return value

    @field_validator("response")
    @classmethod
    def validate_response(cls, value: str) -> str:
        if not value:
            raise ValueError("Enter a response for the requester.")
        return value

    @field_validator("next_steps", mode="before")
    @classmethod
    def strip_next_steps(cls, value: object) -> object:
        """Trim whitespace from next-step entries before validation."""
        if isinstance(value, list):
            return [step.strip() if isinstance(step, str) else step for step in value]
        return value

    @field_validator("next_steps")
    @classmethod
    def validate_next_steps(cls, value: list[str]) -> list[str]:
        cleaned = [step for step in value if step]
        if not cleaned:
            raise ValueError("Enter at least one next step.")
        return cleaned

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: ServiceStatus) -> ServiceStatus:
        if value not in {ServiceStatus.PENDING, ServiceStatus.CLOSED}:
            raise ValueError("Manual triage status must be Pending or Closed.")
        return value


class TriageResultSchema(BaseSchema):
    """Structured LLM response saved onto a ticket."""

    category: ServiceCategory = Field(..., description="The category of the ticket")
    priority: ServicePriority = Field(..., description="The tickets priority level")
    summary: str = Field(..., description="The summary for the ticket")
    response: str = Field(..., description="The response to the ticket")
    next_steps: list[str] = Field(default_factory=list, description="Provided next steps")
    confidence: AIConfidence = Field(..., description="The confidence level service response")

    @field_serializer("priority", "category", "confidence")
    def serialize_to_title(self, item: ServiceCategory | ServicePriority | AIConfidence) -> str:
        return item.value.title()


class RetrievedKBMatchSchema(BaseSchema):
    """Retrieved knowledge-base match used during triage."""

    id: int
    source_name: str
    chunk_text: str
    metadata: dict[str, str | float | int | bool | None] = Field(default_factory=dict)
    similarity: float


class RetrievedTicketMatchSchema(BaseSchema):
    """Retrieved similar-ticket match used during triage."""

    ticket_id: int
    title: str
    combined_text: str
    similarity: float


class TicketAITraceSchema(BaseSchema):
    """Persisted retrieval trace for demo/debug visibility."""

    query_text: str
    kb_matches: list[RetrievedKBMatchSchema] = Field(default_factory=list)
    ticket_matches: list[RetrievedTicketMatchSchema] = Field(default_factory=list)


class TicketResponseSchema(BaseSchema):
    """Ticket payload returned to the UI."""

    id: int = Field(..., description="The unique identifier of the ticket")
    requestor_name: str = Field(..., description="The name of the person who made the request")
    requestor_email: EmailStr = Field(..., description="The email of the person who made the request")
    user_role: UserRole = Field(..., description="The role of the person who made the request")
    title: str = Field(..., description="The title assigned to the ticket")
    description: str = Field(..., description="A brief description of the issue")
    status: ServiceStatus = Field(..., description="The current status of the ticket")
    priority: ServicePriority = Field(..., description="The tickets priority level")
    category: ServiceCategory = Field(..., description="The category of the ticket")
    ai_summary: str | None = Field(default=None, description="The AI summary for the ticket")
    ai_response: str | None = Field(default=None, description="The AI response to the ticket")
    ai_next_steps: list[str] = Field(default_factory=list, description="Next steps provided by the AI")
    manual_summary: str | None = Field(default=None, description="The manual summary for the ticket")
    manual_response: str | None = Field(default=None, description="The human-authored response to the ticket")
    manual_next_steps: list[str] = Field(default_factory=list, description="Next steps provided by a helpdesk worker")
    ai_confidence: AIConfidence | None = Field(default=None, description="The AI's confidence level of its response")
    ai_trace: TicketAITraceSchema | None = Field(
        default=None,
        description="Persisted retrieval trace for the latest AI triage run",
    )
    created_at: datetime | None = Field(default=None, description="When the ticket was created")
    updated_at: datetime | None = Field(default=None, description="When the ticket was last updated")

    @field_serializer("priority", "category", "status", "user_role", "ai_confidence")
    def serialize_to_title(
        self,
        item: ServiceStatus | ServiceCategory | ServicePriority | UserRole | AIConfidence | None,
    ) -> str | None:
        if item is None:
            return None
        return item.value.title()


class TicketUpdateSchema(TicketCreateSchema):
    """Ticket update payload."""

    id: int = Field(..., description="The unique identifier of the ticket")
    status: ServiceStatus | None = Field(default=None, description="An optional status override")
    priority: ServicePriority | None = Field(default=None, description="An optional priority override")
    category: ServiceCategory | None = Field(default=None, description="An optional category override")
    created_at: datetime | None = Field(default=None, description="Optional datetime the ticket was created")
    updated_at: datetime | None = Field(default=None, description="Optional datetime the ticket was updated")
