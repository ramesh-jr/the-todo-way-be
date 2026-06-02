"""User ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.label import Label
    from app.models.section import Section
    from app.models.todo import Todo


class User(Base, TimestampMixin):
    """Single user account for authentication."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    # Relationships
    todos: Mapped[list[Todo]] = relationship(back_populates="user")
    sections: Mapped[list[Section]] = relationship(back_populates="user")
    labels: Mapped[list[Label]] = relationship(back_populates="user")
