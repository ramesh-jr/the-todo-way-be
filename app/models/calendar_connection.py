"""CalendarConnection ORM model.

An external satellite calendar account (Google / Outlook). OAuth tokens are stored
encrypted (Fernet) and never logged.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User

PROVIDER_GOOGLE = "google"
PROVIDER_OUTLOOK = "outlook"

CONNECTION_ACTIVE = "active"
CONNECTION_ERROR = "error"
CONNECTION_DISCONNECTED = "disconnected"


class CalendarConnection(Base, TimestampMixin):
    """A connected external calendar account with sync state."""

    __tablename__ = "calendar_connections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(20))
    account_email: Mapped[str | None] = mapped_column(String(320))

    # Encrypted at rest.
    access_token: Mapped[str | None] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Incremental sync state (Google syncToken / Graph deltaLink).
    sync_token: Mapped[str | None] = mapped_column(Text)
    calendar_id: Mapped[str | None] = mapped_column(String(255))

    status: Mapped[str] = mapped_column(String(20), default=CONNECTION_ACTIVE)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    user: Mapped[User] = relationship(back_populates="calendar_connections")
