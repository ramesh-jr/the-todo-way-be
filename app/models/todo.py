"""Todo ORM model and todo_labels association table."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Index, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.label import Label
    from app.models.reminder import Reminder
    from app.models.section import Section, Subsection
    from app.models.user import User

# Many-to-many association table for todos and labels
todo_labels = Table(
    "todo_labels",
    Base.metadata,
    Column(
        "todo_id",
        ForeignKey("todos.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "label_id",
        ForeignKey("labels.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Todo(Base, TimestampMixin):
    """Core todo item with scheduling, priority, and relationships."""

    __tablename__ = "todos"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    scheduled_date: Mapped[datetime | None] = mapped_column(index=True)
    deadline_date: Mapped[datetime | None] = mapped_column(index=True)
    duration_minutes: Mapped[int | None]
    priority: Mapped[str] = mapped_column(String(2), default="p4")
    location: Mapped[str | None] = mapped_column(String(500))
    is_completed: Mapped[bool] = mapped_column(default=False, index=True)
    completed_at: Mapped[datetime | None]
    section_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sections.id"), index=True
    )
    subsection_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("subsections.id")
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="todos")
    section: Mapped[Section | None] = relationship(back_populates="todos")
    subsection: Mapped[Subsection | None] = relationship(back_populates="todos")
    labels: Mapped[list[Label]] = relationship(
        secondary="todo_labels", back_populates="todos"
    )
    reminders: Mapped[list[Reminder]] = relationship(
        back_populates="todo", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_todos_user_completed", "user_id", "is_completed"),
        Index("ix_todos_user_section", "user_id", "section_id"),
        Index("ix_todos_user_scheduled", "user_id", "scheduled_date"),
    )
