"""Reminder ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.item import Item


class Reminder(Base):
    """Reminder entry for an item, delivered via web-push when scheduled."""

    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), index=True
    )
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    offset_type: Mapped[str] = mapped_column(String(20))  # before_5min, before_1hr, ...

    # Relationships
    item: Mapped[Item] = relationship(back_populates="reminders")
