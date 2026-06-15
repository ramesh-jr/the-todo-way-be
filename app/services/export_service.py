"""Data export: full JSON + human-readable Markdown. The user's data is never a hostage."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.domain import Domain, ReflectionEntry
from app.models.item import Item
from app.models.priority import Priority
from app.models.routine import Routine


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def _row(obj: Any, fields: list[str]) -> dict[str, Any]:
    return {f: _jsonable(getattr(obj, f)) for f in fields}


class ExportService:
    """Assembles a complete, portable export of the user's command center."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def export_json(self, user_id: uuid.UUID) -> dict[str, Any]:
        domains = list(
            await self.db.scalars(
                select(Domain)
                .where(Domain.user_id == user_id)
                .options(selectinload(Domain.standards))
                .order_by(Domain.sort_order)
            )
        )
        items = list(
            await self.db.scalars(
                select(Item)
                .where(Item.user_id == user_id)
                .options(selectinload(Item.labels), selectinload(Item.reminders))
                .order_by(Item.created_at)
            )
        )
        priorities = list(
            await self.db.scalars(
                select(Priority).where(Priority.user_id == user_id)
            )
        )
        routines = list(
            await self.db.scalars(
                select(Routine).where(Routine.user_id == user_id)
            )
        )
        reflections = list(
            await self.db.scalars(
                select(ReflectionEntry)
                .join(Domain, ReflectionEntry.domain_id == Domain.id)
                .where(Domain.user_id == user_id)
            )
        )

        return {
            "exported_at": datetime.now(UTC).isoformat(),
            "version": "v3",
            "domains": [
                {
                    **_row(
                        d,
                        [
                            "id",
                            "name",
                            "slug",
                            "color",
                            "icon",
                            "season",
                            "season_note",
                            "reflection_only",
                        ],
                    ),
                    "standards": [
                        _row(
                            s,
                            ["id", "text", "kind", "cadence", "target", "active"],
                        )
                        for s in d.standards
                    ],
                }
                for d in domains
            ],
            "priorities": [
                _row(p, ["id", "title", "domain_id", "status", "period_start"])
                for p in priorities
            ],
            "routines": [
                _row(r, ["id", "title", "rrule", "domain_id", "active"])
                for r in routines
            ],
            "items": [
                {
                    **_row(
                        i,
                        [
                            "id",
                            "title",
                            "notes",
                            "status",
                            "kind",
                            "domain_id",
                            "priority_id",
                            "energy",
                            "scheduled_at",
                            "duration_minutes",
                            "deadline_at",
                            "urgency",
                            "source",
                            "completed_at",
                        ],
                    ),
                    "context": list(i.context or []),
                    "labels": [lbl.name for lbl in i.labels],
                }
                for i in items
            ],
            "reflections": [
                _row(
                    r,
                    ["id", "domain_id", "standard_id", "rating", "note", "period_start"],
                )
                for r in reflections
            ],
        }

    async def export_markdown(self, user_id: uuid.UUID) -> str:
        data = await self.export_json(user_id)
        lines: list[str] = ["# The Todo Way - Export", ""]
        lines.append(f"_Exported {data['exported_at']}_")
        lines.append("")
        for domain in data["domains"]:
            lines.append(f"## {domain['name']} ({domain['season']})")
            if domain.get("season_note"):
                lines.append(f"> {domain['season_note']}")
            for std in domain["standards"]:
                marker = "[count]" if std["kind"] == "countable" else "[reflect]"
                lines.append(f"- {marker} {std['text']}")
            lines.append("")
        active_items = [i for i in data["items"] if i["status"] != "done"]
        lines.append(f"## Open items ({len(active_items)})")
        for item in active_items:
            lines.append(f"- {item['title']} ({item['status']})")
        return "\n".join(lines)
