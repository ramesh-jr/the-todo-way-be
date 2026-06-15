"""Routine schemas."""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Energy


class RoutineCreate(BaseModel):
    """Create a recurring generator."""

    title: str = Field(..., min_length=1, max_length=280)
    rrule: str = Field(..., min_length=1, max_length=500)
    domain_id: uuid.UUID | None = None
    standard_id: uuid.UUID | None = None
    default_energy: Energy | None = None
    default_context: list[str] = Field(default_factory=list)
    default_duration_minutes: int | None = Field(None, ge=5, le=1440)


class RoutineUpdate(BaseModel):
    """Update a routine."""

    title: str | None = Field(None, min_length=1, max_length=280)
    rrule: str | None = Field(None, min_length=1, max_length=500)
    domain_id: uuid.UUID | None = None
    standard_id: uuid.UUID | None = None
    default_energy: Energy | None = None
    default_context: list[str] | None = None
    default_duration_minutes: int | None = Field(None, ge=5, le=1440)
    active: bool | None = None


class RoutineResponse(BaseModel):
    """A routine."""

    id: uuid.UUID
    domain_id: uuid.UUID | None
    standard_id: uuid.UUID | None
    title: str
    rrule: str
    default_energy: Energy | None
    default_context: list[str]
    default_duration_minutes: int | None
    active: bool
    last_generated_date: date | None
    model_config = ConfigDict(from_attributes=True)


class GenerateResult(BaseModel):
    """Result of materializing due routine instances (grace: missed are skipped)."""

    generated: int
    skipped_missed: int
