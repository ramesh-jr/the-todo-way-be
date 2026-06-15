"""Provider clients for Google Calendar and Microsoft Graph (Outlook).

Each client knows how to build an OAuth authorization URL, exchange/refresh tokens, and
list events incrementally, returning a normalized shape. Real network calls require
configured credentials; without them, building a URL raises a friendly error.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

import httpx

from app.core.config import settings
from app.core.exceptions import BadRequestException


@dataclass
class NormalizedEvent:
    """A provider event mapped to our common shape."""

    external_id: str
    title: str
    start: datetime | None
    end: datetime | None
    calendar_id: str | None = None
    deleted: bool = False


@dataclass
class SyncPage:
    """A page of normalized events plus the next incremental sync token."""

    events: list[NormalizedEvent] = field(default_factory=list)
    next_sync_token: str | None = None


@dataclass
class TokenSet:
    """OAuth tokens returned by a provider."""

    access_token: str
    refresh_token: str | None
    expires_in: int | None


class CalendarClient(Protocol):
    """Common interface implemented by each provider client."""

    provider: str

    def authorization_url(self, state: str) -> str: ...

    async def exchange_code(self, code: str) -> TokenSet: ...

    async def refresh(self, refresh_token: str) -> TokenSet: ...

    async def list_events(
        self, access_token: str, sync_token: str | None
    ) -> SyncPage: ...


def _redirect_uri(provider: str) -> str:
    return f"{settings.app_base_url}/api/v1/calendar/callback/{provider}"


def _parse_dt(value: dict[str, Any] | None) -> datetime | None:
    if not value:
        return None
    raw = value.get("dateTime") or value.get("date")
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


class GoogleCalendarClient:
    """Google Calendar API (calendar.events.readonly)."""

    provider = "google"
    _AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
    _TOKEN = "https://oauth2.googleapis.com/token"  # noqa: S105
    _EVENTS = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    _SCOPE = "https://www.googleapis.com/auth/calendar.events.readonly"

    def _require_creds(self) -> tuple[str, str]:
        if not settings.google_client_id or not settings.google_client_secret:
            raise BadRequestException("Google Calendar is not configured")
        return settings.google_client_id, settings.google_client_secret

    def authorization_url(self, state: str) -> str:
        client_id, _ = self._require_creds()
        params = httpx.QueryParams(
            {
                "client_id": client_id,
                "redirect_uri": _redirect_uri(self.provider),
                "response_type": "code",
                "scope": self._SCOPE,
                "access_type": "offline",
                "prompt": "consent",
                "state": state,
            }
        )
        return f"{self._AUTH}?{params}"

    async def exchange_code(self, code: str) -> TokenSet:
        client_id, client_secret = self._require_creds()
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                self._TOKEN,
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": _redirect_uri(self.provider),
                    "grant_type": "authorization_code",
                },
            )
        return self._token_set(resp)

    async def refresh(self, refresh_token: str) -> TokenSet:
        client_id, client_secret = self._require_creds()
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                self._TOKEN,
                data={
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "refresh_token",
                },
            )
        token = self._token_set(resp)
        if token.refresh_token is None:
            token.refresh_token = refresh_token
        return token

    async def list_events(
        self, access_token: str, sync_token: str | None
    ) -> SyncPage:
        params: dict[str, Any] = {"singleEvents": "true", "maxResults": 250}
        if sync_token:
            params["syncToken"] = sync_token
        else:
            params["timeMin"] = datetime.now().astimezone().isoformat()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                self._EVENTS,
                params=params,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        resp.raise_for_status()
        body: dict[str, Any] = resp.json()
        events: list[NormalizedEvent] = []
        for raw in body.get("items", []):
            events.append(
                NormalizedEvent(
                    external_id=str(raw.get("id")),
                    title=raw.get("summary") or "(untitled)",
                    start=_parse_dt(raw.get("start")),
                    end=_parse_dt(raw.get("end")),
                    deleted=raw.get("status") == "cancelled",
                )
            )
        return SyncPage(events=events, next_sync_token=body.get("nextSyncToken"))

    @staticmethod
    def _token_set(resp: httpx.Response) -> TokenSet:
        resp.raise_for_status()
        body: dict[str, Any] = resp.json()
        return TokenSet(
            access_token=str(body.get("access_token")),
            refresh_token=body.get("refresh_token"),
            expires_in=body.get("expires_in"),
        )


class OutlookCalendarClient:
    """Microsoft Graph calendar (Calendars.Read)."""

    provider = "outlook"
    _AUTH = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    _TOKEN = "https://login.microsoftonline.com/common/oauth2/v2.0/token"  # noqa: S105
    _EVENTS = "https://graph.microsoft.com/v1.0/me/events"
    _SCOPE = "offline_access Calendars.Read"

    def _require_creds(self) -> tuple[str, str]:
        if not settings.ms_client_id or not settings.ms_client_secret:
            raise BadRequestException("Outlook Calendar is not configured")
        return settings.ms_client_id, settings.ms_client_secret

    def authorization_url(self, state: str) -> str:
        client_id, _ = self._require_creds()
        params = httpx.QueryParams(
            {
                "client_id": client_id,
                "redirect_uri": _redirect_uri(self.provider),
                "response_type": "code",
                "scope": self._SCOPE,
                "state": state,
            }
        )
        return f"{self._AUTH}?{params}"

    async def exchange_code(self, code: str) -> TokenSet:
        client_id, client_secret = self._require_creds()
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                self._TOKEN,
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": _redirect_uri(self.provider),
                    "grant_type": "authorization_code",
                    "scope": self._SCOPE,
                },
            )
        return self._token_set(resp)

    async def refresh(self, refresh_token: str) -> TokenSet:
        client_id, client_secret = self._require_creds()
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                self._TOKEN,
                data={
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "refresh_token",
                    "scope": self._SCOPE,
                },
            )
        token = self._token_set(resp)
        if token.refresh_token is None:
            token.refresh_token = refresh_token
        return token

    async def list_events(
        self, access_token: str, sync_token: str | None
    ) -> SyncPage:
        # Graph uses delta links; for simplicity we page the events collection.
        url = sync_token or self._EVENTS
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        resp.raise_for_status()
        body: dict[str, Any] = resp.json()
        events: list[NormalizedEvent] = []
        for raw in body.get("value", []):
            events.append(
                NormalizedEvent(
                    external_id=str(raw.get("id")),
                    title=raw.get("subject") or "(untitled)",
                    start=_parse_dt(raw.get("start")),
                    end=_parse_dt(raw.get("end")),
                    deleted=bool(raw.get("@removed")),
                )
            )
        return SyncPage(
            events=events, next_sync_token=body.get("@odata.deltaLink")
        )

    @staticmethod
    def _token_set(resp: httpx.Response) -> TokenSet:
        resp.raise_for_status()
        body: dict[str, Any] = resp.json()
        return TokenSet(
            access_token=str(body.get("access_token")),
            refresh_token=body.get("refresh_token"),
            expires_in=body.get("expires_in"),
        )


def get_client(provider: str) -> CalendarClient:
    """Return the client for a provider name."""
    if provider == "google":
        return GoogleCalendarClient()
    if provider == "outlook":
        return OutlookCalendarClient()
    raise BadRequestException(f"Unknown calendar provider: {provider}")
