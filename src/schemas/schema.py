"""Application schemas for tickets and AI triage."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_serializer

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
    requestor_email: str = Field(..., description="The email of the person who made the request")
    user_role: UserRole = Field(..., description="The role of the person who made the request")
    title: str = Field(..., description="The title assigned to the ticket")
    description: str = Field(..., description="A brief description of the issue")


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
    requestor_email: str = Field(..., description="The email of the person who made the request")
    user_role: UserRole = Field(..., description="The role of the person who made the request")
    title: str = Field(..., description="The title assigned to the ticket")
    description: str = Field(..., description="A brief description of the issue")
    status: ServiceStatus = Field(..., description="The current status of the ticket")
    priority: ServicePriority = Field(..., description="The tickets priority level")
    category: ServiceCategory = Field(..., description="The category of the ticket")
    ai_summary: str | None = Field(default=None, description="The AI summary for the ticket")
    ai_response: str | None = Field(default=None, description="The AI response to the ticket")
    ai_next_steps: list[str] = Field(default_factory=list, description="Next steps provided by the AI")
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
