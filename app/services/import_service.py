"""Re-import a JSON export into an existing user's account.

Intended for disaster recovery when a managed Postgres restore is unavailable.
Preserves IDs when possible so deep links and habits of reference stay intact.
Does not import calendar OAuth tokens (re-connect calendars after restore).
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, select

from app.models.domain import Domain, ReflectionEntry, Standard

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
from app.models.item import Item, item_labels
from app.models.label import Label
from app.models.priority import Priority
from app.models.reminder import Reminder
from app.models.routine import Routine


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _require_date(value: str | None) -> date:
    parsed = _parse_date(value)
    return parsed if parsed is not None else datetime.now(UTC).date()


def _uuid(value: str | None) -> uuid.UUID | None:
    if not value:
        return None
    return uuid.UUID(value)


class ImportService:
    """Replace the user's command-center data with a v3 JSON export."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def import_json(
        self, user_id: uuid.UUID, payload: dict[str, Any], *, wipe: bool = True
    ) -> dict[str, int]:
        """Import domains/standards/priorities/routines/items/reflections.

        Args:
            user_id: Target account.
            payload: Export produced by ``ExportService.export_json``.
            wipe: If True (default), delete existing user data first.

        Returns:
            Counts of rows imported per entity type.
        """
        if payload.get("version") != "v3":
            raise ValueError("Unsupported export version (expected v3)")

        if wipe:
            await self._wipe_user_data(user_id)

        counts = {
            "domains": 0,
            "standards": 0,
            "priorities": 0,
            "routines": 0,
            "items": 0,
            "reflections": 0,
            "labels": 0,
        }

        for d in payload.get("domains", []):
            domain = Domain(
                id=_uuid(d["id"]) or uuid.uuid4(),
                user_id=user_id,
                name=d["name"],
                slug=d["slug"],
                color=d.get("color") or "#6366F1",
                icon=d.get("icon") or "circle",
                season=d.get("season") or "active",
                season_note=d.get("season_note"),
                reflection_only=bool(d.get("reflection_only", False)),
                sort_order=counts["domains"],
            )
            self.db.add(domain)
            counts["domains"] += 1
            for s in d.get("standards", []):
                self.db.add(
                    Standard(
                        id=_uuid(s["id"]) or uuid.uuid4(),
                        domain_id=domain.id,
                        text=s["text"],
                        kind=s.get("kind") or "countable",
                        cadence=s.get("cadence"),
                        target=s.get("target"),
                        active=bool(s.get("active", True)),
                    )
                )
                counts["standards"] += 1

        await self.db.flush()

        for p in payload.get("priorities", []):
            self.db.add(
                Priority(
                    id=_uuid(p["id"]) or uuid.uuid4(),
                    user_id=user_id,
                    title=p["title"],
                    domain_id=_uuid(p.get("domain_id")),
                    status=p.get("status") or "active",
                    period_start=_require_date(p.get("period_start")),
                )
            )
            counts["priorities"] += 1

        for r in payload.get("routines", []):
            self.db.add(
                Routine(
                    id=_uuid(r["id"]) or uuid.uuid4(),
                    user_id=user_id,
                    title=r["title"],
                    rrule=r.get("rrule") or "FREQ=WEEKLY",
                    domain_id=_uuid(r.get("domain_id")),
                    active=bool(r.get("active", True)),
                )
            )
            counts["routines"] += 1

        await self.db.flush()

        label_cache: dict[str, Label] = {}
        for i in payload.get("items", []):
            item = Item(
                id=_uuid(i["id"]) or uuid.uuid4(),
                user_id=user_id,
                title=i["title"],
                notes=i.get("notes"),
                status=i.get("status") or "inbox",
                kind=i.get("kind") or "task",
                domain_id=_uuid(i.get("domain_id")),
                priority_id=_uuid(i.get("priority_id")),
                energy=i.get("energy"),
                context=i.get("context") or [],
                scheduled_at=_parse_dt(i.get("scheduled_at")),
                duration_minutes=i.get("duration_minutes"),
                deadline_at=_parse_dt(i.get("deadline_at")),
                urgency=i.get("urgency"),
                source=i.get("source") or "manual",
                completed_at=_parse_dt(i.get("completed_at")),
            )
            self.db.add(item)
            counts["items"] += 1

            for name in i.get("labels") or []:
                if name not in label_cache:
                    existing = await self.db.scalar(
                        select(Label).where(
                            Label.user_id == user_id, Label.name == name
                        )
                    )
                    if existing is None:
                        existing = Label(
                            id=uuid.uuid4(), user_id=user_id, name=name
                        )
                        self.db.add(existing)
                        await self.db.flush()
                        counts["labels"] += 1
                    label_cache[name] = existing
                item.labels.append(label_cache[name])

        for r in payload.get("reflections", []):
            domain_id = _uuid(r.get("domain_id"))
            if domain_id is None:
                continue
            self.db.add(
                ReflectionEntry(
                    id=_uuid(r["id"]) or uuid.uuid4(),
                    domain_id=domain_id,
                    standard_id=_uuid(r.get("standard_id")),
                    rating=r.get("rating"),
                    note=r.get("note"),
                    period_start=_require_date(r.get("period_start")),
                )
            )
            counts["reflections"] += 1

        await self.db.commit()
        return counts

    async def _wipe_user_data(self, user_id: uuid.UUID) -> None:
        """Delete command-center rows for the user (keeps the user account)."""
        item_ids = select(Item.id).where(Item.user_id == user_id)
        await self.db.execute(
            delete(Reminder).where(Reminder.item_id.in_(item_ids))
        )
        await self.db.execute(
            delete(item_labels).where(item_labels.c.item_id.in_(item_ids))
        )
        await self.db.execute(delete(Item).where(Item.user_id == user_id))
        await self.db.execute(delete(Priority).where(Priority.user_id == user_id))
        await self.db.execute(delete(Routine).where(Routine.user_id == user_id))
        await self.db.execute(delete(Label).where(Label.user_id == user_id))

        domain_ids = select(Domain.id).where(Domain.user_id == user_id)
        await self.db.execute(
            delete(ReflectionEntry).where(
                ReflectionEntry.domain_id.in_(domain_ids)
            )
        )
        await self.db.execute(
            delete(Standard).where(Standard.domain_id.in_(domain_ids))
        )
        await self.db.execute(delete(Domain).where(Domain.user_id == user_id))
        await self.db.commit()
