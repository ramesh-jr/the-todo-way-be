"""Calendar connection and sync schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.common import CalendarProvider


class CalendarConnectionResponse(BaseModel):
    """A connected external calendar (no secrets exposed)."""

    id: uuid.UUID
    provider: CalendarProvider
    account_email: str | None
    calendar_id: str | None
    status: str
    last_synced_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class OAuthStart(BaseModel):
    """The URL the client should open to begin the OAuth flow."""

    authorization_url: str


class SyncResult(BaseModel):
    """Outcome of an incremental sync."""

    imported: int
    updated: int
    deleted: int
    connections_synced: int
