"""Calendar connection + sync routes (the satellites)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.dependencies import CurrentUser, DbSession
from app.schemas.calendar import (
    CalendarConnectionResponse,
    OAuthStart,
    SyncResult,
)
from app.schemas.common import CalendarProvider
from app.schemas.response import ApiResponse
from app.services.calendar_service import CalendarSyncService

router = APIRouter()


@router.get("/connections")
async def list_connections(
    user: CurrentUser, db: DbSession
) -> ApiResponse[list[CalendarConnectionResponse]]:
    """List connected external calendars (no secrets exposed)."""
    conns = await CalendarSyncService(db).list_connections(user.id)
    return ApiResponse(
        data=[CalendarConnectionResponse.model_validate(c) for c in conns]
    )


@router.post("/connect/{provider}")
async def connect(
    provider: CalendarProvider, user: CurrentUser, db: DbSession
) -> ApiResponse[OAuthStart]:
    """Begin the OAuth flow; the client opens the returned authorization URL."""
    url = CalendarSyncService(db).authorization_url(user.id, provider)
    return ApiResponse(data=OAuthStart(authorization_url=url))


@router.get("/callback/{provider}")
async def callback(
    provider: CalendarProvider, code: str, state: str, db: DbSession
) -> RedirectResponse:
    """OAuth redirect target; stores tokens then returns to the app settings page."""
    await CalendarSyncService(db).handle_callback(provider, code, state)
    return RedirectResponse(url=f"{settings.frontend_base_url}/settings?connected={provider}")


@router.post("/sync")
async def sync(user: CurrentUser, db: DbSession) -> ApiResponse[SyncResult]:
    """Incrementally sync all connected calendars into items (kind=event)."""
    result = await CalendarSyncService(db).sync(user.id)
    return ApiResponse(data=result)


@router.delete("/connections/{connection_id}")
async def disconnect(
    connection_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> ApiResponse[None]:
    """Disconnect an external calendar."""
    await CalendarSyncService(db).disconnect(user.id, connection_id)
    return ApiResponse(data=None)
