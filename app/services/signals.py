"""Calm domain/standard signals.

A "signal" is a gentle tri-state (`on_track` | `needs_attention` | `paused` | `none`),
never a streak or a score. Reflection standards and reflection-only domains are never
measured by activity - they can only be *invited* to reflect (Goodhart guard).
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import (
    SEASON_PAUSED,
    STANDARD_COUNTABLE,
    Domain,
    ReflectionEntry,
    Standard,
)
from app.models.item import STATUS_DONE, Item

_CADENCE_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}


def _week_start(today: date | None = None) -> date:
    today = today or datetime.now(UTC).date()
    return today - timedelta(days=today.weekday())


async def _recent_completed_for_standard(
    db: AsyncSession, user_id: uuid.UUID, standard: Standard
) -> int:
    days = _CADENCE_DAYS.get(standard.cadence or "weekly", 7)
    since = datetime.now(UTC) - timedelta(days=days)
    count = await db.scalar(
        select(func.count())
        .select_from(Item)
        .where(
            Item.user_id == user_id,
            Item.standard_id == standard.id,
            Item.status == STATUS_DONE,
            Item.completed_at >= since,
        )
    )
    return int(count or 0)


def standard_signal(recent_count: int, target: int | None) -> str:
    """Map recent activity vs target onto a calm signal."""
    if target is None:
        return "none"
    return "on_track" if recent_count >= target else "needs_attention"


async def domain_needs_reflection(
    db: AsyncSession, domain: Domain
) -> bool:
    """True if this domain has no reflection entry for the current week."""
    has_reflection_standard = domain.reflection_only or any(
        s.kind != STANDARD_COUNTABLE for s in domain.standards
    )
    if not has_reflection_standard:
        return False
    existing = await db.scalar(
        select(func.count())
        .select_from(ReflectionEntry)
        .where(
            ReflectionEntry.domain_id == domain.id,
            ReflectionEntry.period_start == _week_start(),
        )
    )
    return int(existing or 0) == 0


async def recent_wins_for_domain(
    db: AsyncSession, user_id: uuid.UUID, domain_id: uuid.UUID, days: int = 7
) -> int:
    """Count completed items in a domain over the last `days` (for the wins-first view)."""
    since = datetime.now(UTC) - timedelta(days=days)
    count = await db.scalar(
        select(func.count())
        .select_from(Item)
        .where(
            Item.user_id == user_id,
            Item.domain_id == domain_id,
            Item.status == STATUS_DONE,
            Item.completed_at >= since,
        )
    )
    return int(count or 0)


async def standard_signals_for_domain(
    db: AsyncSession, user_id: uuid.UUID, domain: Domain
) -> list[tuple[Standard, str, int]]:
    """Return (standard, signal, recent_count) for each countable standard.

    Reflection standards are intentionally excluded - they are never measured.
    Paused domains report `paused` for everything.
    """
    out: list[tuple[Standard, str, int]] = []
    for standard in domain.standards:
        if standard.kind != STANDARD_COUNTABLE or not standard.active:
            continue
        if domain.season == SEASON_PAUSED:
            out.append((standard, "paused", 0))
            continue
        recent = await _recent_completed_for_standard(db, user_id, standard)
        out.append((standard, standard_signal(recent, standard.target), recent))
    return out


def aggregate_domain_signal(
    domain: Domain, standard_signals: list[tuple[Standard, str, int]]
) -> str:
    """Roll up a domain's standard signals into one calm signal."""
    if domain.season == SEASON_PAUSED:
        return "paused"
    if domain.reflection_only or not standard_signals:
        return "none"
    if any(sig == "needs_attention" for _, sig, _ in standard_signals):
        return "needs_attention"
    return "on_track"
