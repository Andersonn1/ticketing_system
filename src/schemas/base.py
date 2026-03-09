"""Base Schema For All Schema Objects"""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    """Base Schema Model"""

    model_config = ConfigDict(
        extra="forbid", alias_generator=to_camel, populate_by_name=True
    )


class AuditMixin:
    """Audit Mixin"""

    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When was the entity created",
    )
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When was the entity last updated",
    )
