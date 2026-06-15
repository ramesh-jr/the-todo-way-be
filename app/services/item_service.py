"""Item business logic: capture, clarify, schedule, complete, CRUD, filtering."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException
from app.models.item import (
    STATUS_ACTIVE,
    STATUS_DONE,
    STATUS_INBOX,
    STATUS_SCHEDULED,
    STATUS_SOMEDAY,
    Item,
)
from app.models.label import Label
from app.schemas.item import (
    CaptureInput,
    ClarifyInput,
    ItemCreate,
    ItemUpdate,
    ScheduleInput,
)


def _now() -> datetime:
    return datetime.now(UTC)


class ItemService:
    """All queries and mutations for items."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # -- helpers ------------------------------------------------------------
    @staticmethod
    def _loaded() -> tuple[Any, ...]:
        return (selectinload(Item.labels), selectinload(Item.reminders))

    async def _get_owned(self, user_id: uuid.UUID, item_id: uuid.UUID) -> Item:
        item = await self.db.scalar(
            select(Item)
            .where(Item.id == item_id, Item.user_id == user_id)
            .options(*self._loaded())
        )
        if item is None:
            raise NotFoundException("Item")
        return item

    async def _resolve_labels(
        self, user_id: uuid.UUID, label_ids: list[uuid.UUID]
    ) -> list[Label]:
        if not label_ids:
            return []
        result = await self.db.scalars(
            select(Label).where(Label.user_id == user_id, Label.id.in_(label_ids))
        )
        return list(result)

    # -- capture ------------------------------------------------------------
    async def capture(self, user_id: uuid.UUID, data: CaptureInput) -> Item:
        """Quick capture -> a raw inbox item (clarified later)."""
        item = Item(
            user_id=user_id,
            title=data.title.strip(),
            notes=data.notes,
            status=STATUS_INBOX,
            context=[],
        )
        self.db.add(item)
        await self.db.commit()
        return await self._get_owned(user_id, item.id)

    # -- create -------------------------------------------------------------
    async def create(self, user_id: uuid.UUID, data: ItemCreate) -> Item:
        item = Item(
            user_id=user_id,
            title=data.title.strip(),
            notes=data.notes,
            status=data.status,
            kind=data.kind,
            domain_id=data.domain_id,
            priority_id=data.priority_id,
            standard_id=data.standard_id,
            energy=data.energy,
            context=data.context,
            scheduled_at=data.scheduled_at,
            duration_minutes=data.duration_minutes,
            deadline_at=data.deadline_at,
            urgency=data.urgency,
        )
        if data.scheduled_at and data.status == STATUS_ACTIVE:
            item.status = STATUS_SCHEDULED
        item.labels = await self._resolve_labels(user_id, data.label_ids)
        self.db.add(item)
        await self.db.commit()
        return await self._get_owned(user_id, item.id)

    # -- list ---------------------------------------------------------------
    async def list(
        self,
        user_id: uuid.UUID,
        *,
        status: str | None = None,
        domain_id: uuid.UUID | None = None,
        priority_id: uuid.UUID | None = None,
        energy: str | None = None,
        context: str | None = None,
        kind: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        max_minutes: int | None = None,
    ) -> list[Item]:
        stmt = select(Item).where(Item.user_id == user_id).options(*self._loaded())
        if status:
            stmt = stmt.where(Item.status == status)
        if domain_id:
            stmt = stmt.where(Item.domain_id == domain_id)
        if priority_id:
            stmt = stmt.where(Item.priority_id == priority_id)
        if energy:
            stmt = stmt.where(Item.energy == energy)
        if kind:
            stmt = stmt.where(Item.kind == kind)
        if date_from:
            stmt = stmt.where(Item.scheduled_at >= date_from)
        if date_to:
            stmt = stmt.where(Item.scheduled_at <= date_to)
        if max_minutes is not None:
            stmt = stmt.where(
                (Item.duration_minutes.is_(None))
                | (Item.duration_minutes <= max_minutes)
            )
        stmt = stmt.order_by(Item.created_at.desc())
        result = await self.db.scalars(stmt)
        items = list(result)
        # Context tags are stored as a JSON list; filter in Python (small dataset).
        if context:
            items = [i for i in items if context in (i.context or [])]
        return items

    async def get(self, user_id: uuid.UUID, item_id: uuid.UUID) -> Item:
        return await self._get_owned(user_id, item_id)

    # -- update -------------------------------------------------------------
    async def update(
        self, user_id: uuid.UUID, item_id: uuid.UUID, data: ItemUpdate
    ) -> Item:
        item = await self._get_owned(user_id, item_id)
        payload = data.model_dump(exclude_unset=True)
        label_ids = payload.pop("label_ids", None)
        for key, value in payload.items():
            setattr(item, key, value)
        if label_ids is not None:
            item.labels = await self._resolve_labels(user_id, label_ids)
        await self.db.commit()
        return await self._get_owned(user_id, item_id)

    async def delete(self, user_id: uuid.UUID, item_id: uuid.UUID) -> None:
        item = await self._get_owned(user_id, item_id)
        await self.db.delete(item)
        await self.db.commit()

    # -- clarify (move out of inbox) ---------------------------------------
    async def clarify(
        self, user_id: uuid.UUID, item_id: uuid.UUID, data: ClarifyInput
    ) -> Item:
        item = await self._get_owned(user_id, item_id)
        payload = data.model_dump(exclude_unset=True)
        target_status = payload.pop("target_status", None)
        for key, value in payload.items():
            setattr(item, key, value)
        if target_status:
            item.status = target_status
        elif item.scheduled_at:
            item.status = STATUS_SCHEDULED
        else:
            item.status = STATUS_ACTIVE
        await self.db.commit()
        return await self._get_owned(user_id, item_id)

    # -- complete / schedule / someday -------------------------------------
    async def toggle_complete(self, user_id: uuid.UUID, item_id: uuid.UUID) -> Item:
        item = await self._get_owned(user_id, item_id)
        if item.status == STATUS_DONE:
            item.status = STATUS_SCHEDULED if item.scheduled_at else STATUS_ACTIVE
            item.completed_at = None
        else:
            item.status = STATUS_DONE
            item.completed_at = _now()
        await self.db.commit()
        return await self._get_owned(user_id, item_id)

    async def schedule(
        self, user_id: uuid.UUID, item_id: uuid.UUID, data: ScheduleInput
    ) -> Item:
        item = await self._get_owned(user_id, item_id)
        item.scheduled_at = data.scheduled_at
        item.duration_minutes = data.duration_minutes
        if item.status in (STATUS_INBOX, STATUS_ACTIVE):
            item.status = STATUS_SCHEDULED
        await self.db.commit()
        return await self._get_owned(user_id, item_id)

    async def mark_someday(self, user_id: uuid.UUID, item_id: uuid.UUID) -> Item:
        item = await self._get_owned(user_id, item_id)
        item.status = STATUS_SOMEDAY
        item.someday_reviewed_at = _now()
        await self.db.commit()
        return await self._get_owned(user_id, item_id)
