"""Priority routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.priority import (
    PriorityCreate,
    PriorityResponse,
    PriorityStatusUpdate,
    PriorityUpdate,
)
from app.schemas.response import ApiResponse
from app.services.priority_service import PriorityService

router = APIRouter()


@router.get("")
async def list_priorities(
    user: CurrentUser,
    db: DbSession,
    current_only: bool = Query(True),
) -> ApiResponse[list[PriorityResponse]]:
    """List priorities (current period by default)."""
    priorities = await PriorityService(db).list(user.id, current_only=current_only)
    return ApiResponse(data=[PriorityResponse.model_validate(p) for p in priorities])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_priority(
    data: PriorityCreate, user: CurrentUser, db: DbSession
) -> ApiResponse[PriorityResponse]:
    """Create a priority for the current period."""
    priority = await PriorityService(db).create(user.id, data)
    return ApiResponse(data=PriorityResponse.model_validate(priority))


@router.put("/{priority_id}")
async def update_priority(
    priority_id: uuid.UUID, data: PriorityUpdate, user: CurrentUser, db: DbSession
) -> ApiResponse[PriorityResponse]:
    """Update a priority."""
    priority = await PriorityService(db).update(user.id, priority_id, data)
    return ApiResponse(data=PriorityResponse.model_validate(priority))


@router.patch("/{priority_id}/status")
async def set_priority_status(
    priority_id: uuid.UUID,
    data: PriorityStatusUpdate,
    user: CurrentUser,
    db: DbSession,
) -> ApiResponse[PriorityResponse]:
    """Mark a priority done/dropped/active."""
    priority = await PriorityService(db).set_status(user.id, priority_id, data)
    return ApiResponse(data=PriorityResponse.model_validate(priority))


@router.delete("/{priority_id}")
async def delete_priority(
    priority_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> ApiResponse[None]:
    """Delete a priority."""
    await PriorityService(db).delete(user.id, priority_id)
    return ApiResponse(data=None)
