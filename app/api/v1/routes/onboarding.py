"""Onboarding routes: seed default domains + starter standards."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.response import ApiResponse
from app.services.seed_service import SeedService

router = APIRouter()


@router.post("/seed")
async def seed(user: CurrentUser, db: DbSession) -> ApiResponse[dict[str, int]]:
    """Create starter domains (Family reflection-only) if none exist."""
    created = await SeedService(db).seed_defaults(user.id)
    return ApiResponse(data={"created": created})


@router.get("/status")
async def onboarding_status(
    user: CurrentUser, db: DbSession
) -> ApiResponse[dict[str, bool]]:
    """Whether the user has any domains yet (used to show onboarding)."""
    has_domains = await SeedService(db).has_domains(user.id)
    return ApiResponse(data={"has_domains": has_domains})
