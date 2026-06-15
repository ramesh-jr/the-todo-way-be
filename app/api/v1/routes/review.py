"""Review ritual routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.response import ApiResponse
from app.schemas.review import (
    ReviewComplete,
    ReviewDefer,
    ReviewResponse,
    ReviewStatus,
)
from app.services.review_service import ReviewService

router = APIRouter()


@router.get("/status")
async def review_status(
    user: CurrentUser, db: DbSession
) -> ApiResponse[ReviewStatus]:
    """Whether a review is due, plus gentle re-entry + deferral context."""
    status_data = await ReviewService(db).status(user.id)
    return ApiResponse(data=status_data)


@router.post("/complete")
async def complete_review(
    data: ReviewComplete, user: CurrentUser, db: DbSession
) -> ApiResponse[ReviewResponse]:
    """Mark the review complete."""
    review = await ReviewService(db).complete(user.id, data)
    return ApiResponse(data=ReviewResponse.model_validate(review))


@router.post("/defer")
async def defer_review(
    data: ReviewDefer, user: CurrentUser, db: DbSession
) -> ApiResponse[ReviewResponse]:
    """Defer the review with an optional comment (a conscious choice)."""
    review = await ReviewService(db).defer(user.id, data)
    return ApiResponse(data=ReviewResponse.model_validate(review))
