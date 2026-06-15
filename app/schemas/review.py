"""Review ritual schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ReviewType


class ReviewComplete(BaseModel):
    """Mark a review as completed."""

    type: ReviewType = "weekly"


class ReviewDefer(BaseModel):
    """Defer a review with an optional comment (a conscious choice, not avoidance)."""

    type: ReviewType = "weekly"
    reason: str | None = Field(None, max_length=280)
    until: datetime | None = None


class ReviewStatus(BaseModel):
    """Whether a review is due, plus gentle re-entry context."""

    is_due: bool
    last_completed_at: datetime | None
    days_since_last: int | None
    deferred_reason: str | None
    deferred_until: datetime | None
    # Gentle re-entry after a long gap ("welcome back").
    long_gap: bool


class ReviewResponse(BaseModel):
    """A review record."""

    id: uuid.UUID
    type: ReviewType
    status: str
    deferred_reason: str | None
    deferred_until: datetime | None
    completed_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
