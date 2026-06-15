"""Domain, standard, reflection, and dashboard schemas."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Cadence, DomainSignal, Season, StandardKind


class StandardCreate(BaseModel):
    """Create a standard for a domain."""

    text: str = Field(..., min_length=1, max_length=280)
    kind: StandardKind = "reflection"
    cadence: Cadence | None = None
    target: int | None = Field(None, ge=1, le=100)
    sort_order: int = 0


class StandardUpdate(BaseModel):
    """Update a standard."""

    text: str | None = Field(None, min_length=1, max_length=280)
    cadence: Cadence | None = None
    target: int | None = Field(None, ge=1, le=100)
    active: bool | None = None
    sort_order: int | None = None


class StandardResponse(BaseModel):
    """A standard with its current (calm) signal."""

    id: uuid.UUID
    domain_id: uuid.UUID
    text: str
    kind: StandardKind
    cadence: Cadence | None
    target: int | None
    active: bool
    sort_order: int
    model_config = ConfigDict(from_attributes=True)


class DomainCreate(BaseModel):
    """Create a life domain."""

    name: str = Field(..., min_length=1, max_length=120)
    color: str = Field("#6366F1", pattern=r"^#[0-9a-fA-F]{6}$")
    icon: str = Field("circle", max_length=40)
    sort_order: int = 0
    reflection_only: bool = False


class DomainUpdate(BaseModel):
    """Update a life domain."""

    name: str | None = Field(None, min_length=1, max_length=120)
    color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    icon: str | None = Field(None, max_length=40)
    sort_order: int | None = None


class SeasonUpdate(BaseModel):
    """Change a domain's season (a conscious choice, logged)."""

    season: Season
    note: str | None = Field(None, max_length=280)


class DomainResponse(BaseModel):
    """A life domain with its standards."""

    id: uuid.UUID
    name: str
    slug: str
    color: str
    icon: str
    sort_order: int
    season: Season
    season_note: str | None
    season_changed_at: datetime | None
    reflection_only: bool
    standards: list[StandardResponse]
    model_config = ConfigDict(from_attributes=True)


class ReflectionCreate(BaseModel):
    """Add a gentle 1-5 self-rating + optional note."""

    standard_id: uuid.UUID | None = None
    rating: int | None = Field(None, ge=1, le=5)
    note: str | None = None
    period_start: date | None = None


class ReflectionResponse(BaseModel):
    """A reflection entry."""

    id: uuid.UUID
    domain_id: uuid.UUID
    standard_id: uuid.UUID | None
    rating: int | None
    note: str | None
    period_start: date
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TrendPoint(BaseModel):
    """A single point in a reflection trend series."""

    period_start: date
    rating: int | None
    note: str | None


# ---- Conscious-attention dashboard ----------------------------------------


class StandardSignal(BaseModel):
    """A countable standard's calm signal (never a streak or score)."""

    standard_id: uuid.UUID
    text: str
    signal: DomainSignal
    recent_count: int
    target: int | None
    cadence: Cadence | None


class DomainCard(BaseModel):
    """A domain as shown on the dashboard."""

    domain: DomainResponse
    signal: DomainSignal
    standard_signals: list[StandardSignal]
    needs_reflection: bool
    recent_wins: int


class DashboardResponse(BaseModel):
    """The conscious-attention dashboard, leading with focus and wins."""

    # 1. What you chose to focus on
    focus_priorities: list[uuid.UUID]
    recent_wins: int
    # 2. Intentional choices (seasons)
    maintenance_domains: list[uuid.UUID]
    paused_domains: list[uuid.UUID]
    # 3. Gentle invitations (never failure)
    domains: list[DomainCard]
