"""Review ORM model.

Records of the review ritual. A review can be `completed` or `deferred` (with a comment),
so deferral is a conscious choice rather than silent avoidance.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.user import User

REVIEW_DAILY = "daily"
REVIEW_WEEKLY = "weekly"

REVIEW_COMPLETED = "completed"
REVIEW_DEFERRED = "deferred"


class Review(Base):
    """A daily or weekly review ritual record."""

    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(20), default=REVIEW_WEEKLY)
    status: Mapped[str] = mapped_column(String(20), default=REVIEW_COMPLETED)
    deferred_reason: Mapped[str | None] = mapped_column(String(280))
    deferred_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="reviews")
