"""Item routes: capture, clarify, schedule, complete, and CRUD."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.common import Energy, ItemKind, ItemStatus
from app.schemas.item import (
    CaptureInput,
    ClarifyInput,
    ItemCreate,
    ItemResponse,
    ItemUpdate,
    ScheduleInput,
)
from app.schemas.response import ApiResponse
from app.services.item_service import ItemService

router = APIRouter()


@router.post("/capture", status_code=status.HTTP_201_CREATED)
async def capture(
    data: CaptureInput, user: CurrentUser, db: DbSession
) -> ApiResponse[ItemResponse]:
    """Quick capture into the inbox - title only, clarified later."""
    item = await ItemService(db).capture(user.id, data)
    return ApiResponse(data=ItemResponse.model_validate(item))


@router.get("")
async def list_items(
    user: CurrentUser,
    db: DbSession,
    status_filter: ItemStatus | None = Query(None, alias="status"),
    domain_id: uuid.UUID | None = None,
    priority_id: uuid.UUID | None = None,
    energy: Energy | None = None,
    context: str | None = None,
    kind: ItemKind | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    max_minutes: int | None = None,
) -> ApiResponse[list[ItemResponse]]:
    """List items with rich filtering (status, domain, energy, context, time, ...)."""
    items = await ItemService(db).list(
        user.id,
        status=status_filter,
        domain_id=domain_id,
        priority_id=priority_id,
        energy=energy,
        context=context,
        kind=kind,
        date_from=date_from,
        date_to=date_to,
        max_minutes=max_minutes,
    )
    return ApiResponse(data=[ItemResponse.model_validate(i) for i in items])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_item(
    data: ItemCreate, user: CurrentUser, db: DbSession
) -> ApiResponse[ItemResponse]:
    """Create a fully-specified item."""
    item = await ItemService(db).create(user.id, data)
    return ApiResponse(data=ItemResponse.model_validate(item))


@router.get("/{item_id}")
async def get_item(
    item_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> ApiResponse[ItemResponse]:
    """Get a single item."""
    item = await ItemService(db).get(user.id, item_id)
    return ApiResponse(data=ItemResponse.model_validate(item))


@router.put("/{item_id}")
async def update_item(
    item_id: uuid.UUID, data: ItemUpdate, user: CurrentUser, db: DbSession
) -> ApiResponse[ItemResponse]:
    """Partial update."""
    item = await ItemService(db).update(user.id, item_id, data)
    return ApiResponse(data=ItemResponse.model_validate(item))


@router.delete("/{item_id}")
async def delete_item(
    item_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> ApiResponse[None]:
    """Delete an item."""
    await ItemService(db).delete(user.id, item_id)
    return ApiResponse(data=None)


@router.patch("/{item_id}/clarify")
async def clarify_item(
    item_id: uuid.UUID, data: ClarifyInput, user: CurrentUser, db: DbSession
) -> ApiResponse[ItemResponse]:
    """Clarify an inbox capture and move it out of the inbox."""
    item = await ItemService(db).clarify(user.id, item_id, data)
    return ApiResponse(data=ItemResponse.model_validate(item))


@router.patch("/{item_id}/complete")
async def complete_item(
    item_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> ApiResponse[ItemResponse]:
    """Toggle completion."""
    item = await ItemService(db).toggle_complete(user.id, item_id)
    return ApiResponse(data=ItemResponse.model_validate(item))


@router.patch("/{item_id}/schedule")
async def schedule_item(
    item_id: uuid.UUID, data: ScheduleInput, user: CurrentUser, db: DbSession
) -> ApiResponse[ItemResponse]:
    """Place the item on the calendar (drag-and-drop)."""
    item = await ItemService(db).schedule(user.id, item_id, data)
    return ApiResponse(data=ItemResponse.model_validate(item))


@router.patch("/{item_id}/someday")
async def someday_item(
    item_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> ApiResponse[ItemResponse]:
    """Move an item to the gentle 'someday' shelf."""
    item = await ItemService(db).mark_someday(user.id, item_id)
    return ApiResponse(data=ItemResponse.model_validate(item))
