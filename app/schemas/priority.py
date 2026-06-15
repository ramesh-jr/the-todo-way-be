"""Priority schemas."""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PriorityStatus


class PriorityCreate(BaseModel):
    """Create a priority for the current period."""

    title: str = Field(..., min_length=1, max_length=280)
    domain_id: uuid.UUID | None = None
    horizon: str = "week"
    period_start: date | None = None
    sort_order: int = 0


class PriorityUpdate(BaseModel):
    """Update a priority."""

    title: str | None = Field(None, min_length=1, max_length=280)
    domain_id: uuid.UUID | None = None
    status: PriorityStatus | None = None
    sort_order: int | None = None


class PriorityStatusUpdate(BaseModel):
    """Set a priority's status."""

    status: PriorityStatus


class PriorityResponse(BaseModel):
    """A priority."""

    id: uuid.UUID
    domain_id: uuid.UUID | None
    title: str
    horizon: str
    status: PriorityStatus
    period_start: date
    sort_order: int
    model_config = ConfigDict(from_attributes=True)
