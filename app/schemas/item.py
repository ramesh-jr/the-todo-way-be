"""Item schemas: capture, create, clarify, schedule, update, response."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Energy, ItemKind, ItemStatus, Source, Urgency
from app.schemas.label import LabelResponse, ReminderResponse


class CaptureInput(BaseModel):
    """Quick capture - title only (optionally with a raw string for NL parsing)."""

    title: str = Field(..., min_length=1, max_length=500)
    notes: str | None = None
    raw: str | None = Field(
        None, description="Optional raw text for natural-language parsing"
    )


class ItemCreate(BaseModel):
    """Create a fully-specified item."""

    title: str = Field(..., min_length=1, max_length=500)
    notes: str | None = None
    status: ItemStatus = "active"
    kind: ItemKind = "task"
    domain_id: uuid.UUID | None = None
    priority_id: uuid.UUID | None = None
    standard_id: uuid.UUID | None = None
    energy: Energy | None = None
    context: list[str] = Field(default_factory=list)
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(None, ge=5, le=1440)
    deadline_at: datetime | None = None
    urgency: Urgency = "normal"
    label_ids: list[uuid.UUID] = Field(default_factory=list)


class ItemUpdate(BaseModel):
    """Partial update for an item."""

    title: str | None = Field(None, min_length=1, max_length=500)
    notes: str | None = None
    status: ItemStatus | None = None
    kind: ItemKind | None = None
    domain_id: uuid.UUID | None = None
    priority_id: uuid.UUID | None = None
    standard_id: uuid.UUID | None = None
    energy: Energy | None = None
    context: list[str] | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(None, ge=5, le=1440)
    deadline_at: datetime | None = None
    urgency: Urgency | None = None
    label_ids: list[uuid.UUID] | None = None


class ClarifyInput(BaseModel):
    """Clarify an inbox capture: assign domain/priority/energy/context, then move out."""

    domain_id: uuid.UUID | None = None
    priority_id: uuid.UUID | None = None
    energy: Energy | None = None
    context: list[str] | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(None, ge=5, le=1440)
    urgency: Urgency | None = None
    # Where the item lands after clarifying. Defaults to active (or scheduled if a time set).
    target_status: ItemStatus | None = None


class ScheduleInput(BaseModel):
    """Place an item on the calendar (drag-and-drop)."""

    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=5, le=1440)


class ItemResponse(BaseModel):
    """An item in any state."""

    id: uuid.UUID
    title: str
    notes: str | None
    status: ItemStatus
    kind: ItemKind
    domain_id: uuid.UUID | None
    priority_id: uuid.UUID | None
    routine_id: uuid.UUID | None
    standard_id: uuid.UUID | None
    energy: Energy | None
    context: list[str]
    scheduled_at: datetime | None
    duration_minutes: int | None
    deadline_at: datetime | None
    urgency: Urgency
    rrule: str | None
    source: Source
    external_id: str | None
    external_calendar_id: str | None
    someday_reviewed_at: datetime | None
    completed_at: datetime | None
    labels: list[LabelResponse]
    reminders: list[ReminderResponse]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
