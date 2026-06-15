"""Routine ORM model.

A Routine is a recurring generator (workout 3x/week, weekly review, monthly bills)
defined by an RFC-5545 RRULE. It materializes Item instances so the user never re-enters
them. Grace by default: generation only fills the current horizon forward - missed past
occurrences are never backfilled into a pile of overdue guilt.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Routine(Base, TimestampMixin):
    """A recurring item generator that upholds a standard."""

    __tablename__ = "routines"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    domain_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("domains.id", ondelete="SET NULL"), index=True
    )
    standard_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("standards.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(280))
    rrule: Mapped[str] = mapped_column(String(500))
    default_energy: Mapped[str | None] = mapped_column(String(10))
    default_context: Mapped[list[str]] = mapped_column(JSON, default=list)
    default_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(default=True)
    last_generated_date: Mapped[date | None] = mapped_column(Date)

    # Relationships
    user: Mapped[User] = relationship(back_populates="routines")
