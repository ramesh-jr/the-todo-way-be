"""User ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.calendar_connection import CalendarConnection
    from app.models.domain import Domain
    from app.models.item import Item
    from app.models.label import Label
    from app.models.priority import Priority
    from app.models.push import PushSubscription
    from app.models.review import Review
    from app.models.routine import Routine


class User(Base, TimestampMixin):
    """Single user account for authentication and recovery."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    # Account recovery (data trust). Recovery code is hashed, never stored plain.
    recovery_email: Mapped[str | None] = mapped_column(String(320))
    recovery_code_hash: Mapped[str | None] = mapped_column(String(255))
    recovery_code_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    # Relationships
    domains: Mapped[list[Domain]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    items: Mapped[list[Item]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    priorities: Mapped[list[Priority]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    routines: Mapped[list[Routine]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    labels: Mapped[list[Label]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    calendar_connections: Mapped[list[CalendarConnection]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    reviews: Mapped[list[Review]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    push_subscriptions: Mapped[list[PushSubscription]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
