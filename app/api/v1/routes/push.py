"""Web Push subscription routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.push import PushSubscribe, VapidKey
from app.schemas.response import ApiResponse
from app.services.push_service import PushService

router = APIRouter()


@router.get("/vapid-public-key")
async def vapid_public_key(
    user: CurrentUser, db: DbSession
) -> ApiResponse[VapidKey]:
    """The public VAPID key the browser uses to subscribe (null if unconfigured)."""
    return ApiResponse(data=VapidKey(public_key=PushService(db).vapid_public_key()))


@router.post("/subscribe")
async def subscribe(
    data: PushSubscribe, user: CurrentUser, db: DbSession
) -> ApiResponse[dict[str, bool]]:
    """Register a browser Web Push subscription."""
    await PushService(db).subscribe(user.id, data)
    return ApiResponse(data={"subscribed": True})


@router.delete("/subscribe")
async def unsubscribe(
    endpoint: str, user: CurrentUser, db: DbSession
) -> ApiResponse[dict[str, bool]]:
    """Remove a browser Web Push subscription."""
    await PushService(db).unsubscribe(user.id, endpoint)
    return ApiResponse(data={"subscribed": False})
