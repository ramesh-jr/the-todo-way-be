"""Nudge engine: calm, dismissible, rate-limited invitations - never guilt or streaks.

Surfaces at most one prominent nudge. Paused domains are excluded everywhere. The four
nudge kinds are: weekly-review-due, unclarified-inbox, overcommitment, someday-decay.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import STATUS_INBOX, STATUS_SCHEDULED, STATUS_SOMEDAY, Item
from app.schemas.nudge import Nudge, NudgeList
from app.services.review_service import ReviewService

# Tunables (sensible defaults; calm by design).
UNCLARIFIED_COUNT_THRESHOLD = 5
UNCLARIFIED_AGE_DAYS = 3
OVERCOMMIT_MINUTES = 10 * 60  # a day fuller than ~10h of commitments
SOMEDAY_DECAY_DAYS = 30


class NudgeService:
    """Computes the gentle nudges shown across the app."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def compute(self, user_id: uuid.UUID) -> NudgeList:
        candidates: list[Nudge] = []

        review = await self._weekly_review_nudge(user_id)
        if review:
            candidates.append(review)

        inbox = await self._unclarified_inbox_nudge(user_id)
        if inbox:
            candidates.append(inbox)

        overcommit = await self._overcommitment_nudge(user_id)
        if overcommit:
            candidates.append(overcommit)

        someday = await self._someday_decay_nudge(user_id)
        if someday:
            candidates.append(someday)

        if not candidates:
            return NudgeList(primary=None, others=[])
        return NudgeList(primary=candidates[0], others=candidates[1:])

    async def _weekly_review_nudge(self, user_id: uuid.UUID) -> Nudge | None:
        status = await ReviewService(self.db).status(user_id)
        if not status.is_due:
            return None
        if status.long_gap:
            return Nudge(
                kind="weekly_review",
                title="Welcome back",
                message="It's been a while. Want a gentle 2-minute reset?",
            )
        return Nudge(
            kind="weekly_review",
            title="Weekly review",
            message="A quiet moment to look at the week ahead?",
        )

    async def _unclarified_inbox_nudge(self, user_id: uuid.UUID) -> Nudge | None:
        cutoff = datetime.now(UTC) - timedelta(days=UNCLARIFIED_AGE_DAYS)
        count = await self.db.scalar(
            select(func.count())
            .select_from(Item)
            .where(
                Item.user_id == user_id,
                Item.status == STATUS_INBOX,
                Item.created_at <= cutoff,
            )
        )
        n = int(count or 0)
        if n < UNCLARIFIED_COUNT_THRESHOLD:
            return None
        return Nudge(
            kind="unclarified_inbox",
            title="A few things are waiting",
            message="Some captures have been sitting a while - a 2-minute sort?",
            count=n,
        )

    async def _overcommitment_nudge(self, user_id: uuid.UUID) -> Nudge | None:
        start = datetime.now(UTC)
        end = start + timedelta(days=7)
        result = await self.db.scalars(
            select(Item).where(
                Item.user_id == user_id,
                Item.status == STATUS_SCHEDULED,
                Item.scheduled_at >= start,
                Item.scheduled_at <= end,
            )
        )
        by_day: dict[date, int] = defaultdict(int)
        for item in result:
            if item.scheduled_at:
                by_day[item.scheduled_at.date()] += item.duration_minutes or 30
        for day, minutes in sorted(by_day.items()):
            if minutes > OVERCOMMIT_MINUTES:
                return Nudge(
                    kind="overcommitment",
                    title="That day looks full",
                    message="One day is packed tighter than it may feel doable. "
                    "Want to move something?",
                    count=minutes,
                    on_date=day,
                )
        return None

    async def _someday_decay_nudge(self, user_id: uuid.UUID) -> Nudge | None:
        cutoff = datetime.now(UTC) - timedelta(days=SOMEDAY_DECAY_DAYS)
        count = await self.db.scalar(
            select(func.count())
            .select_from(Item)
            .where(
                Item.user_id == user_id,
                Item.status == STATUS_SOMEDAY,
                Item.someday_reviewed_at <= cutoff,
            )
        )
        n = int(count or 0)
        if n == 0:
            return None
        return Nudge(
            kind="someday_decay",
            title="Still relevant?",
            message="A few 'someday' items have rested a while. Keep or let go?",
            count=n,
        )
