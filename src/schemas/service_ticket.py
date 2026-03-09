"""IT Service Ticket Schemas"""

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from src.schemas.base import AuditMixin, BaseSchema


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


class ServiceTicketCreate(BaseSchema):
    """The Service Ticket Create Schema"""

    urgency: ServiceUrgency = Field(..., description="The urgency of the ticket matter")
    category: ServiceCategory = Field(
        ..., description="The category the ticket belongs"
    )
    description: str = Field(..., description="A brief description of the issue")
    first_occurrence: datetime = Field(..., description="When did the problem begin")
    received_error_message: bool = Field(
        default=False, description="If the user has received an error message"
    )
    error_message_details: str | None = Field(
        default=None, description="Details from the error message if received"
    )
    assignee: str = Field(..., description="Who is the ticket assigned too")


class ServiceTicketUpdate(ServiceTicketCreate, AuditMixin):
    """The Service Ticket Update Schema"""

    id: int = Field(..., description="The unique identifier of the ticket")


class ServiceTicket(ServiceTicketUpdate):
    """The Service Ticket Schema"""

    ...
