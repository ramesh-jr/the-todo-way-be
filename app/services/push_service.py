"""Web Push (VAPID) subscription management and delivery."""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.push import PushSubscription
from app.schemas.push import PushSubscribe


class PushService:
    """Stores browser subscriptions and sends gentle reminder notifications."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def vapid_public_key(self) -> str | None:
        return settings.vapid_public_key

    async def subscribe(
        self, user_id: uuid.UUID, data: PushSubscribe
    ) -> PushSubscription:
        existing = await self.db.scalar(
            select(PushSubscription).where(
                PushSubscription.endpoint == data.endpoint
            )
        )
        if existing:
            existing.p256dh = data.keys.p256dh
            existing.auth = data.keys.auth
            existing.user_id = user_id
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        sub = PushSubscription(
            user_id=user_id,
            endpoint=data.endpoint,
            p256dh=data.keys.p256dh,
            auth=data.keys.auth,
        )
        self.db.add(sub)
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def unsubscribe(self, user_id: uuid.UUID, endpoint: str) -> None:
        await self.db.execute(
            delete(PushSubscription).where(
                PushSubscription.user_id == user_id,
                PushSubscription.endpoint == endpoint,
            )
        )
        await self.db.commit()

    async def send(self, user_id: uuid.UUID, title: str, body: str) -> int:
        """Send a gentle notification to all of the user's subscriptions.

        Returns the number of successful deliveries. No-op (0) if VAPID is unconfigured.
        """
        if not settings.vapid_private_key:
            return 0
        # Imported lazily so the app boots without the optional dependency configured.
        from pywebpush import WebPushException, webpush

        subs = list(
            await self.db.scalars(
                select(PushSubscription).where(
                    PushSubscription.user_id == user_id
                )
            )
        )
        payload = json.dumps({"title": title, "body": body})
        sent = 0
        for sub in subs:
            info: dict[str, Any] = {
                "endpoint": sub.endpoint,
                "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
            }
            try:
                webpush(
                    subscription_info=info,
                    data=payload,
                    vapid_private_key=settings.vapid_private_key,
                    vapid_claims={"sub": settings.vapid_subject},
                )
                sent += 1
            except WebPushException:
                # Stale subscription - drop it quietly.
                await self.db.delete(sub)
        await self.db.commit()
        return sent
