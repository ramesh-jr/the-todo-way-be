"""Label and reminder schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LabelCreate(BaseModel):
    """Create a color tag."""

    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(..., pattern=r"^#[0-9a-fA-F]{6}$")


class LabelResponse(BaseModel):
    """A color tag."""

    id: uuid.UUID
    name: str
    color: str
    model_config = ConfigDict(from_attributes=True)


class ReminderCreate(BaseModel):
    """Create a reminder for an item."""

    remind_at: datetime
    offset_type: str = Field(..., max_length=20)


class ReminderResponse(BaseModel):
    """A reminder entry."""

    id: uuid.UUID
    remind_at: datetime
    offset_type: str
    model_config = ConfigDict(from_attributes=True)
