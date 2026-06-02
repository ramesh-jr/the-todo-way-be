"""Reminder ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.todo import Todo


class Reminder(Base):
    """Reminder entry for a todo (stored, not delivered in MVP)."""

    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    todo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("todos.id"), index=True
    )
    remind_at: Mapped[datetime]
    type: Mapped[str] = mapped_column(String(20))  # before_5min, before_15min, etc.

    # Relationships
    todo: Mapped[Todo] = relationship(back_populates="reminders")
