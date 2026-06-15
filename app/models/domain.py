"""Domain, Standard, ReflectionEntry, and DomainStateLog ORM models.

A Domain is a life area (Family, Health, Career, ...). It is a *dashboard*, not a
to-do list: you watch it, you do not "complete" it. Each domain carries a small set of
Standards (what "good enough" looks like) and a season state (active/maintenance/paused).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, utcnow

if TYPE_CHECKING:
    from app.models.user import User

# Season states. `paused` silences all prompts/nudges; `maintenance` softens cadence.
SEASON_ACTIVE = "active"
SEASON_MAINTENANCE = "maintenance"
SEASON_PAUSED = "paused"

# Standard kinds. Reflection standards are never counted/checkboxed (Goodhart guard).
STANDARD_COUNTABLE = "countable"
STANDARD_REFLECTION = "reflection"


class Domain(Base, TimestampMixin):
    """A life domain shown on the conscious-attention dashboard."""

    __tablename__ = "domains"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(120))
    color: Mapped[str] = mapped_column(String(7), default="#6366F1")
    icon: Mapped[str] = mapped_column(String(40), default="circle")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Season / conscious choice.
    season: Mapped[str] = mapped_column(String(20), default=SEASON_ACTIVE)
    season_note: Mapped[str | None] = mapped_column(String(280))
    season_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Reflection-only domains (e.g. Family) never get countable standards or a
    # slipping signal. The app can only invite reflection, never report failure.
    reflection_only: Mapped[bool] = mapped_column(default=False)

    # Relationships
    user: Mapped[User] = relationship(back_populates="domains")
    standards: Mapped[list[Standard]] = relationship(
        back_populates="domain", cascade="all, delete-orphan"
    )
    reflections: Mapped[list[ReflectionEntry]] = relationship(
        back_populates="domain", cascade="all, delete-orphan"
    )
    state_logs: Mapped[list[DomainStateLog]] = relationship(
        back_populates="domain", cascade="all, delete-orphan"
    )


class Standard(Base, TimestampMixin):
    """What "good enough" looks like for a domain.

    `countable` standards (e.g. "Exercise 3x/week") get a light on-track signal.
    `reflection` standards (relationships, presence, meaning) are captured as a 1-5
    self-rating + note and shown as a trend - never red/green.
    """

    __tablename__ = "standards"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    domain_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("domains.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(String(280))
    kind: Mapped[str] = mapped_column(String(20), default=STANDARD_REFLECTION)
    cadence: Mapped[str | None] = mapped_column(String(20))  # daily|weekly|monthly
    target: Mapped[int | None] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    domain: Mapped[Domain] = relationship(back_populates="standards")
    reflections: Mapped[list[ReflectionEntry]] = relationship(
        back_populates="standard", cascade="all, delete-orphan"
    )


class ReflectionEntry(Base):
    """A gentle periodic self-rating (1-5) + optional note for a domain/standard."""

    __tablename__ = "reflection_entries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    domain_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("domains.id", ondelete="CASCADE"), index=True
    )
    standard_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("standards.id", ondelete="CASCADE"), index=True
    )
    rating: Mapped[int | None] = mapped_column(Integer)  # 1-5
    note: Mapped[str | None] = mapped_column(Text)
    period_start: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    # Relationships
    domain: Mapped[Domain] = relationship(back_populates="reflections")
    standard: Mapped[Standard | None] = relationship(back_populates="reflections")


class DomainStateLog(Base):
    """Audit trail of season changes, so reviews can reflect intentional choices."""

    __tablename__ = "domain_state_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    domain_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("domains.id", ondelete="CASCADE"), index=True
    )
    from_state: Mapped[str] = mapped_column(String(20))
    to_state: Mapped[str] = mapped_column(String(20))
    note: Mapped[str | None] = mapped_column(String(280))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    # Relationships
    domain: Mapped[Domain] = relationship(back_populates="state_logs")
