"""Seed default domains and gentle starter standards for onboarding.

The Family domain is reflection-only by design - no counts, no checkboxes, no slipping.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import (
    STANDARD_COUNTABLE,
    STANDARD_REFLECTION,
    Domain,
    Standard,
)

# Each tuple: (name, color, icon, reflection_only, [standards])
# A standard is (text, kind, cadence, target).
_DEFAULTS: list[tuple[str, str, str, bool, list[tuple[str, str, str | None, int | None]]]] = [
    (
        "Health",
        "#10B981",
        "heart-pulse",
        False,
        [
            ("Exercise 3x/week", STANDARD_COUNTABLE, "weekly", 3),
            ("Sleep reasonably", STANDARD_REFLECTION, None, None),
            ("Don't delay important checkups", STANDARD_COUNTABLE, "monthly", 1),
        ],
    ),
    (
        "Family",
        "#F59E0B",
        "users",
        True,  # reflection-only: relationships are never measured
        [
            ("How connected did this week feel?", STANDARD_REFLECTION, None, None),
        ],
    ),
    (
        "Career",
        "#6366F1",
        "briefcase",
        False,
        [
            ("Clear weekly priorities set", STANDARD_COUNTABLE, "weekly", 1),
            ("No major stakeholder surprises", STANDARD_REFLECTION, None, None),
            ("Some growth action", STANDARD_REFLECTION, None, None),
        ],
    ),
    (
        "Home",
        "#8B5CF6",
        "house",
        False,
        [
            ("Stay on top of essentials", STANDARD_REFLECTION, None, None),
        ],
    ),
    (
        "Personal",
        "#EC4899",
        "sparkles",
        False,
        [
            ("Time for something that's just mine", STANDARD_REFLECTION, None, None),
        ],
    ),
]


class SeedService:
    """Creates the default domains for a new account."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def has_domains(self, user_id: uuid.UUID) -> bool:
        count = await self.db.scalar(
            select(func.count())
            .select_from(Domain)
            .where(Domain.user_id == user_id)
        )
        return int(count or 0) > 0

    async def seed_defaults(self, user_id: uuid.UUID) -> int:
        """Create starter domains + standards if the user has none. Returns count."""
        if await self.has_domains(user_id):
            return 0
        created = 0
        for order, (name, color, icon, reflection_only, standards) in enumerate(
            _DEFAULTS
        ):
            domain = Domain(
                user_id=user_id,
                name=name,
                slug=name.lower(),
                color=color,
                icon=icon,
                sort_order=order,
                reflection_only=reflection_only,
            )
            self.db.add(domain)
            await self.db.flush()
            for s_order, (text, kind, cadence, target) in enumerate(standards):
                self.db.add(
                    Standard(
                        domain_id=domain.id,
                        text=text,
                        kind=kind,
                        cadence=cadence,
                        target=target,
                        sort_order=s_order,
                    )
                )
            created += 1
        await self.db.commit()
        return created
