"""Calendar connection + incremental sync orchestration.

External events are stored as Items (`kind=event`, `source=provider`) so tasks and
meetings live together on one calendar. OAuth tokens are encrypted at rest.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.core.security import decrypt_secret, encrypt_secret
from app.models.calendar_connection import (
    CONNECTION_ACTIVE,
    CONNECTION_ERROR,
    CalendarConnection,
)
from app.models.item import (
    KIND_EVENT,
    STATUS_SCHEDULED,
    Item,
)
from app.schemas.calendar import SyncResult
from app.services.calendar_clients import NormalizedEvent, TokenSet, get_client


class CalendarSyncService:
    """Manages connected calendars and pulls their events into items."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_connections(
        self, user_id: uuid.UUID
    ) -> list[CalendarConnection]:
        result = await self.db.scalars(
            select(CalendarConnection).where(
                CalendarConnection.user_id == user_id
            )
        )
        return list(result)

    def authorization_url(self, user_id: uuid.UUID, provider: str) -> str:
        client = get_client(provider)
        # Single-user app: the user id is a sufficient, opaque state value.
        return client.authorization_url(state=str(user_id))

    async def handle_callback(
        self, provider: str, code: str, state: str
    ) -> CalendarConnection:
        try:
            user_id = uuid.UUID(state)
        except ValueError as exc:
            raise BadRequestException("Invalid OAuth state") from exc
        client = get_client(provider)
        tokens = await client.exchange_code(code)
        return await self._upsert_connection(user_id, provider, tokens)

    async def _upsert_connection(
        self, user_id: uuid.UUID, provider: str, tokens: TokenSet
    ) -> CalendarConnection:
        conn = await self.db.scalar(
            select(CalendarConnection).where(
                CalendarConnection.user_id == user_id,
                CalendarConnection.provider == provider,
            )
        )
        expires_at = (
            datetime.now(UTC) + timedelta(seconds=tokens.expires_in)
            if tokens.expires_in
            else None
        )
        if conn is None:
            conn = CalendarConnection(user_id=user_id, provider=provider)
            self.db.add(conn)
        conn.access_token = encrypt_secret(tokens.access_token)
        if tokens.refresh_token:
            conn.refresh_token = encrypt_secret(tokens.refresh_token)
        conn.token_expires_at = expires_at
        conn.status = CONNECTION_ACTIVE
        await self.db.commit()
        await self.db.refresh(conn)
        return conn

    async def disconnect(
        self, user_id: uuid.UUID, connection_id: uuid.UUID
    ) -> None:
        conn = await self.db.scalar(
            select(CalendarConnection).where(
                CalendarConnection.id == connection_id,
                CalendarConnection.user_id == user_id,
            )
        )
        if conn is None:
            raise NotFoundException("Calendar connection")
        await self.db.delete(conn)
        await self.db.commit()

    async def sync(self, user_id: uuid.UUID) -> SyncResult:
        connections = await self.list_connections(user_id)
        imported = updated = deleted = synced = 0

        for conn in connections:
            if conn.status != CONNECTION_ACTIVE or not conn.access_token:
                continue
            client = get_client(conn.provider)
            access = decrypt_secret(conn.access_token)
            try:
                page = await client.list_events(access, conn.sync_token)
            except httpx.HTTPStatusError:
                # Try a one-time token refresh, then mark errored if it still fails.
                refreshed = await self._maybe_refresh(conn)
                if not refreshed:
                    conn.status = CONNECTION_ERROR
                    continue
                access = decrypt_secret(conn.access_token)
                try:
                    page = await client.list_events(access, conn.sync_token)
                except httpx.HTTPError:
                    conn.status = CONNECTION_ERROR
                    continue
            except httpx.HTTPError:
                conn.status = CONNECTION_ERROR
                continue

            for event in page.events:
                outcome = await self._apply_event(user_id, conn.provider, event)
                if outcome == "imported":
                    imported += 1
                elif outcome == "updated":
                    updated += 1
                elif outcome == "deleted":
                    deleted += 1

            conn.sync_token = page.next_sync_token or conn.sync_token
            conn.last_synced_at = datetime.now(UTC)
            synced += 1

        await self.db.commit()
        return SyncResult(
            imported=imported,
            updated=updated,
            deleted=deleted,
            connections_synced=synced,
        )

    async def _maybe_refresh(self, conn: CalendarConnection) -> bool:
        if not conn.refresh_token:
            return False
        client = get_client(conn.provider)
        try:
            tokens = await client.refresh(decrypt_secret(conn.refresh_token))
        except httpx.HTTPError:
            return False
        conn.access_token = encrypt_secret(tokens.access_token)
        if tokens.refresh_token:
            conn.refresh_token = encrypt_secret(tokens.refresh_token)
        if tokens.expires_in:
            conn.token_expires_at = datetime.now(UTC) + timedelta(
                seconds=tokens.expires_in
            )
        return True

    async def _apply_event(
        self, user_id: uuid.UUID, provider: str, event: NormalizedEvent
    ) -> str:
        existing = await self.db.scalar(
            select(Item).where(
                Item.user_id == user_id,
                Item.source == provider,
                Item.external_id == event.external_id,
            )
        )
        if event.deleted:
            if existing:
                await self.db.delete(existing)
                return "deleted"
            return "noop"

        duration = None
        if event.start and event.end:
            duration = max(5, int((event.end - event.start).total_seconds() // 60))

        if existing:
            existing.title = event.title
            existing.scheduled_at = event.start
            existing.duration_minutes = duration
            return "updated"

        self.db.add(
            Item(
                user_id=user_id,
                title=event.title,
                status=STATUS_SCHEDULED,
                kind=KIND_EVENT,
                source=provider,
                external_id=event.external_id,
                external_calendar_id=event.calendar_id,
                scheduled_at=event.start,
                duration_minutes=duration,
                context=[],
            )
        )
        return "imported"
