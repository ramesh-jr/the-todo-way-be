"""Standard update/delete routes (creation lives under /domains/{id}/standards)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.domain import StandardResponse, StandardUpdate
from app.schemas.response import ApiResponse
from app.services.standard_service import StandardService

router = APIRouter()


@router.put("/{standard_id}")
async def update_standard(
    standard_id: uuid.UUID, data: StandardUpdate, user: CurrentUser, db: DbSession
) -> ApiResponse[StandardResponse]:
    """Update a standard (reflection standards never gain a cadence/target)."""
    standard = await StandardService(db).update(user.id, standard_id, data)
    return ApiResponse(data=StandardResponse.model_validate(standard))


@router.delete("/{standard_id}")
async def delete_standard(
    standard_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> ApiResponse[None]:
    """Delete a standard."""
    await StandardService(db).delete(user.id, standard_id)
    return ApiResponse(data=None)
