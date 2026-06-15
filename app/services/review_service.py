"""Review ritual business logic: status, complete, defer (with comment)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import (
    REVIEW_COMPLETED,
    REVIEW_DEFERRED,
    Review,
)
from app.schemas.review import ReviewComplete, ReviewDefer, ReviewStatus

_DUE_AFTER_DAYS = 7
_LONG_GAP_DAYS = 14


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


class ReviewService:
    """The lightweight, skippable review ritual."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _latest(self, user_id: uuid.UUID, status: str) -> Review | None:
        return await self.db.scalar(
            select(Review)
            .where(Review.user_id == user_id, Review.status == status)
            .order_by(desc(Review.created_at))
            .limit(1)
        )

    async def status(self, user_id: uuid.UUID) -> ReviewStatus:
        last_completed = await self._latest(user_id, REVIEW_COMPLETED)
        last_deferred = await self._latest(user_id, REVIEW_DEFERRED)
        now = datetime.now(UTC)

        completed_at = _aware(last_completed.completed_at) if last_completed else None
        days_since = (now - completed_at).days if completed_at else None

        # A still-pending deferral suppresses the nudge until its `until` time.
        deferred_reason: str | None = None
        deferred_until: datetime | None = None
        if last_deferred and (
            last_completed is None
            or _aware(last_deferred.created_at) > _aware(last_completed.created_at)  # type: ignore[operator]
        ):
            deferred_reason = last_deferred.deferred_reason
            deferred_until = _aware(last_deferred.deferred_until)

        is_due = days_since is None or days_since >= _DUE_AFTER_DAYS
        if deferred_until and deferred_until > now:
            is_due = False

        long_gap = days_since is None or days_since >= _LONG_GAP_DAYS

        return ReviewStatus(
            is_due=is_due,
            last_completed_at=completed_at,
            days_since_last=days_since,
            deferred_reason=deferred_reason,
            deferred_until=deferred_until,
            long_gap=long_gap,
        )

    async def complete(self, user_id: uuid.UUID, data: ReviewComplete) -> Review:
        review = Review(
            user_id=user_id,
            type=data.type,
            status=REVIEW_COMPLETED,
            completed_at=datetime.now(UTC),
        )
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def defer(self, user_id: uuid.UUID, data: ReviewDefer) -> Review:
        review = Review(
            user_id=user_id,
            type=data.type,
            status=REVIEW_DEFERRED,
            deferred_reason=data.reason,
            deferred_until=data.until,
        )
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        return review
