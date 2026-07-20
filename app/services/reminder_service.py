"""Due-reminder delivery via Web Push.

Run periodically (cron / EventBridge / ``make reminders``). Reminders fire once
and are deleted after a successful send attempt (or after logging when VAPID
is unset, so the queue does not grow forever in local).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reminder import Reminder
from app.services.push_service import PushService

logger = logging.getLogger(__name__)


class ReminderService:
    """Finds due reminders and delivers gentle push notifications."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def deliver_due(self, *, now: datetime | None = None) -> dict[str, int]:
        """Send push for all reminders with ``remind_at <= now``.

        Returns counts: ``due``, ``sent``, ``skipped``.
        """
        when = now or datetime.now(UTC)
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)

        due = list(
            await self.db.scalars(
                select(Reminder)
                .where(Reminder.remind_at <= when)
                .options(selectinload(Reminder.item))
                .order_by(Reminder.remind_at)
            )
        )
        push = PushService(self.db)
        sent = 0
        skipped = 0

        for reminder in due:
            item = reminder.item
            if item is None:
                await self.db.delete(reminder)
                skipped += 1
                continue

            title = "Gentle reminder"
            body = item.title
            delivered = await push.send(item.user_id, title, body)
            if delivered == 0:
                # VAPID unset or no subscriptions — still clear the row so the
                # queue cannot accumulate indefinitely in local/dev.
                logger.info(
                    "Reminder due for item %s (%s) — no push delivery",
                    item.id,
                    item.title,
                )
                skipped += 1
            else:
                sent += delivered
            await self.db.delete(reminder)

        await self.db.commit()
        return {"due": len(due), "sent": sent, "skipped": skipped}
