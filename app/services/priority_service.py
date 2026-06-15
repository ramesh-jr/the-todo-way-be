"""Priority business logic."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.priority import Priority
from app.schemas.priority import (
    PriorityCreate,
    PriorityStatusUpdate,
    PriorityUpdate,
)


def _week_start() -> date:
    today = datetime.now(UTC).date()
    return today - timedelta(days=today.weekday())


class PriorityService:
    """CRUD for the week's priorities."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_owned(
        self, user_id: uuid.UUID, priority_id: uuid.UUID
    ) -> Priority:
        priority = await self.db.scalar(
            select(Priority).where(
                Priority.id == priority_id, Priority.user_id == user_id
            )
        )
        if priority is None:
            raise NotFoundException("Priority")
        return priority

    async def list(
        self, user_id: uuid.UUID, *, current_only: bool = True
    ) -> list[Priority]:
        stmt = select(Priority).where(Priority.user_id == user_id)
        if current_only:
            stmt = stmt.where(Priority.period_start >= _week_start())
        stmt = stmt.order_by(Priority.sort_order, Priority.created_at)
        result = await self.db.scalars(stmt)
        return list(result)

    async def create(self, user_id: uuid.UUID, data: PriorityCreate) -> Priority:
        priority = Priority(
            user_id=user_id,
            title=data.title.strip(),
            domain_id=data.domain_id,
            horizon=data.horizon,
            period_start=data.period_start or _week_start(),
            sort_order=data.sort_order,
        )
        self.db.add(priority)
        await self.db.commit()
        await self.db.refresh(priority)
        return priority

    async def update(
        self, user_id: uuid.UUID, priority_id: uuid.UUID, data: PriorityUpdate
    ) -> Priority:
        priority = await self._get_owned(user_id, priority_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(priority, key, value)
        await self.db.commit()
        await self.db.refresh(priority)
        return priority

    async def set_status(
        self, user_id: uuid.UUID, priority_id: uuid.UUID, data: PriorityStatusUpdate
    ) -> Priority:
        priority = await self._get_owned(user_id, priority_id)
        priority.status = data.status
        await self.db.commit()
        await self.db.refresh(priority)
        return priority

    async def delete(self, user_id: uuid.UUID, priority_id: uuid.UUID) -> None:
        priority = await self._get_owned(user_id, priority_id)
        await self.db.delete(priority)
        await self.db.commit()
