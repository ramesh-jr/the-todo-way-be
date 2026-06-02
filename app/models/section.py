"""Section and Subsection ORM models."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.todo import Todo
    from app.models.user import User


class Section(Base, TimestampMixin):
    """Top-level grouping for todos (like Todoist Projects)."""

    __tablename__ = "sections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(default=0)

    # Relationships
    user: Mapped[User] = relationship(back_populates="sections")
    subsections: Mapped[list[Subsection]] = relationship(
        back_populates="section", cascade="all, delete-orphan"
    )
    todos: Mapped[list[Todo]] = relationship(back_populates="section")


class Subsection(Base):
    """Nested grouping within a section."""

    __tablename__ = "subsections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    section_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sections.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(default=0)

    # Relationships
    section: Mapped[Section] = relationship(back_populates="subsections")
    todos: Mapped[list[Todo]] = relationship(back_populates="subsection")
