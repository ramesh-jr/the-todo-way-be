"""Item ORM model and item_labels association table.

An Item is everything captured and everything you actually do: inbox captures, next
actions, scheduled tasks, and synced external calendar events. `kind` distinguishes
movable tasks (mine) from events (commitments done to me).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.label import Label
    from app.models.reminder import Reminder
    from app.models.user import User

# Item lifecycle. `inbox` = captured, not yet clarified.
STATUS_INBOX = "inbox"
STATUS_ACTIVE = "active"
STATUS_SCHEDULED = "scheduled"
STATUS_DONE = "done"
STATUS_SOMEDAY = "someday"

KIND_TASK = "task"
KIND_EVENT = "event"

SOURCE_MANUAL = "manual"
SOURCE_GOOGLE = "google"
SOURCE_OUTLOOK = "outlook"


item_labels = Table(
    "item_labels",
    Base.metadata,
    Column(
        "item_id",
        ForeignKey("items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "label_id",
        ForeignKey("labels.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Item(Base, TimestampMixin):
    """A captured thought, a next action, a scheduled task, or an external event."""

    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(20), default=STATUS_INBOX, index=True)
    kind: Mapped[str] = mapped_column(String(20), default=KIND_TASK)

    # Hierarchy links (all optional - an inbox capture has none of these yet).
    domain_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("domains.id", ondelete="SET NULL"), index=True
    )
    priority_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("priorities.id", ondelete="SET NULL"), index=True
    )
    routine_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("routines.id", ondelete="SET NULL"), index=True
    )
    # Countable standards only - reflection standards are never credited by activity.
    standard_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("standards.id", ondelete="SET NULL"), index=True
    )

    # Energy & context: not all time is equal.
    energy: Mapped[str | None] = mapped_column(String(10))  # low|medium|high
    context: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Scheduling.
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    urgency: Mapped[str] = mapped_column(String(10), default="normal")
    rrule: Mapped[str | None] = mapped_column(String(500))

    # Source / external sync.
    source: Mapped[str] = mapped_column(String(20), default=SOURCE_MANUAL)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    external_calendar_id: Mapped[str | None] = mapped_column(String(255))

    # Grace mechanics.
    someday_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    user: Mapped[User] = relationship(back_populates="items")
    labels: Mapped[list[Label]] = relationship(
        secondary=item_labels, back_populates="items"
    )
    reminders: Mapped[list[Reminder]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_items_user_status", "user_id", "status"),
        Index("ix_items_user_domain", "user_id", "domain_id"),
        Index("ix_items_user_scheduled", "user_id", "scheduled_at"),
    )
