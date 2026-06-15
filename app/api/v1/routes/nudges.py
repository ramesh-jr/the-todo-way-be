"""Nudge routes - calm, dismissible invitations."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.nudge import NudgeList
from app.schemas.response import ApiResponse
from app.services.nudge_service import NudgeService

router = APIRouter()


@router.get("")
async def list_nudges(user: CurrentUser, db: DbSession) -> ApiResponse[NudgeList]:
    """Return the current gentle nudges (at most one prominent)."""
    nudges = await NudgeService(db).compute(user.id)
    return ApiResponse(data=nudges)
