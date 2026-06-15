"""Priority ORM model.

A Priority is "what matters this period" (default horizon: the week). It belongs to a
domain and is the level the user actively manages - Today and Review revolve around it.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User

PRIORITY_ACTIVE = "active"
PRIORITY_DONE = "done"
PRIORITY_DROPPED = "dropped"


class Priority(Base, TimestampMixin):
    """A focus for the current period."""

    __tablename__ = "priorities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    domain_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("domains.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(280))
    horizon: Mapped[str] = mapped_column(String(20), default="week")
    status: Mapped[str] = mapped_column(String(20), default=PRIORITY_ACTIVE)
    period_start: Mapped[date] = mapped_column(Date, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    user: Mapped[User] = relationship(back_populates="priorities")
