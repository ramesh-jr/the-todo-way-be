"""Domain business logic: CRUD, seasons, dashboard, reflections."""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException
from app.models.domain import (
    SEASON_MAINTENANCE,
    SEASON_PAUSED,
    Domain,
    DomainStateLog,
    ReflectionEntry,
)
from app.models.priority import PRIORITY_ACTIVE, Priority
from app.schemas.domain import (
    DomainCreate,
    DomainUpdate,
    ReflectionCreate,
    SeasonUpdate,
    TrendPoint,
)
from app.services import signals


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "domain"


def _week_start() -> datetime:
    today = datetime.now(UTC).date()
    from datetime import timedelta

    return datetime.combine(
        today - timedelta(days=today.weekday()), datetime.min.time(), tzinfo=UTC
    )


class DomainService:
    """All queries and mutations for domains, standards-as-a-set, and reflections."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_owned(self, user_id: uuid.UUID, domain_id: uuid.UUID) -> Domain:
        domain = await self.db.scalar(
            select(Domain)
            .where(Domain.id == domain_id, Domain.user_id == user_id)
            .options(selectinload(Domain.standards))
        )
        if domain is None:
            raise NotFoundException("Domain")
        return domain

    async def list(self, user_id: uuid.UUID) -> list[Domain]:
        result = await self.db.scalars(
            select(Domain)
            .where(Domain.user_id == user_id)
            .options(selectinload(Domain.standards))
            .order_by(Domain.sort_order, Domain.name)
        )
        return list(result)

    async def get(self, user_id: uuid.UUID, domain_id: uuid.UUID) -> Domain:
        return await self._get_owned(user_id, domain_id)

    async def create(self, user_id: uuid.UUID, data: DomainCreate) -> Domain:
        domain = Domain(
            user_id=user_id,
            name=data.name.strip(),
            slug=_slugify(data.name),
            color=data.color,
            icon=data.icon,
            sort_order=data.sort_order,
            reflection_only=data.reflection_only,
        )
        self.db.add(domain)
        await self.db.commit()
        return await self._get_owned(user_id, domain.id)

    async def update(
        self, user_id: uuid.UUID, domain_id: uuid.UUID, data: DomainUpdate
    ) -> Domain:
        domain = await self._get_owned(user_id, domain_id)
        payload = data.model_dump(exclude_unset=True)
        if "name" in payload and payload["name"]:
            domain.slug = _slugify(payload["name"])
        for key, value in payload.items():
            setattr(domain, key, value)
        await self.db.commit()
        return await self._get_owned(user_id, domain_id)

    async def delete(self, user_id: uuid.UUID, domain_id: uuid.UUID) -> None:
        domain = await self._get_owned(user_id, domain_id)
        await self.db.delete(domain)
        await self.db.commit()

    async def set_season(
        self, user_id: uuid.UUID, domain_id: uuid.UUID, data: SeasonUpdate
    ) -> Domain:
        """Change a domain's season and log it (a conscious choice, not failure)."""
        domain = await self._get_owned(user_id, domain_id)
        if domain.season != data.season:
            self.db.add(
                DomainStateLog(
                    domain_id=domain.id,
                    from_state=domain.season,
                    to_state=data.season,
                    note=data.note,
                )
            )
        domain.season = data.season
        domain.season_note = data.note
        domain.season_changed_at = datetime.now(UTC)
        await self.db.commit()
        return await self._get_owned(user_id, domain_id)

    # -- reflections --------------------------------------------------------
    async def add_reflection(
        self, user_id: uuid.UUID, domain_id: uuid.UUID, data: ReflectionCreate
    ) -> ReflectionEntry:
        domain = await self._get_owned(user_id, domain_id)
        period = data.period_start or _week_start().date()
        entry = ReflectionEntry(
            domain_id=domain.id,
            standard_id=data.standard_id,
            rating=data.rating,
            note=data.note,
            period_start=period,
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def trend(
        self, user_id: uuid.UUID, domain_id: uuid.UUID, limit: int = 12
    ) -> list[TrendPoint]:
        await self._get_owned(user_id, domain_id)
        result = await self.db.scalars(
            select(ReflectionEntry)
            .where(ReflectionEntry.domain_id == domain_id)
            .order_by(ReflectionEntry.period_start.desc())
            .limit(limit)
        )
        entries = list(result)
        entries.reverse()
        return [
            TrendPoint(
                period_start=e.period_start, rating=e.rating, note=e.note
            )
            for e in entries
        ]

    # -- dashboard data -----------------------------------------------------
    async def dashboard_data(self, user_id: uuid.UUID) -> dict[str, object]:
        """Assemble the conscious-attention dashboard (focus + wins first)."""
        domains = await self.list(user_id)

        focus = await self.db.scalars(
            select(Priority.id).where(
                Priority.user_id == user_id,
                Priority.status == PRIORITY_ACTIVE,
                Priority.period_start >= _week_start().date(),
            )
        )
        focus_ids = list(focus)

        total_wins = 0
        cards: list[dict[str, object]] = []
        maintenance: list[uuid.UUID] = []
        paused: list[uuid.UUID] = []

        for domain in domains:
            if domain.season == SEASON_MAINTENANCE:
                maintenance.append(domain.id)
            elif domain.season == SEASON_PAUSED:
                paused.append(domain.id)

            std_signals = await signals.standard_signals_for_domain(
                self.db, user_id, domain
            )
            wins = await signals.recent_wins_for_domain(self.db, user_id, domain.id)
            total_wins += wins
            needs_reflection = (
                domain.season != SEASON_PAUSED
                and await signals.domain_needs_reflection(self.db, domain)
            )
            cards.append(
                {
                    "domain": domain,
                    "signal": signals.aggregate_domain_signal(domain, std_signals),
                    "standard_signals": std_signals,
                    "needs_reflection": needs_reflection,
                    "recent_wins": wins,
                }
            )

        return {
            "focus_priorities": focus_ids,
            "recent_wins": total_wins,
            "maintenance_domains": maintenance,
            "paused_domains": paused,
            "cards": cards,
        }
