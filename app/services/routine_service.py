"""Routine business logic: RRULE-driven generation with grace by default.

Grace: when materializing instances we only fill forward from the later of
(last_generated_date, today). Missed past occurrences are NEVER backfilled into a pile of
overdue guilt - they are simply skipped.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from dateutil import rrule as dateutil_rrule
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.item import KIND_TASK, SOURCE_MANUAL, STATUS_SCHEDULED, Item
from app.models.routine import Routine
from app.schemas.routine import RoutineCreate, RoutineUpdate

# How far forward to materialize instances in one generation pass.
_GENERATION_HORIZON_DAYS = 14


class RoutineService:
    """CRUD and instance generation for routines."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_owned(
        self, user_id: uuid.UUID, routine_id: uuid.UUID
    ) -> Routine:
        routine = await self.db.scalar(
            select(Routine).where(
                Routine.id == routine_id, Routine.user_id == user_id
            )
        )
        if routine is None:
            raise NotFoundException("Routine")
        return routine

    @staticmethod
    def _parse_rrule(rule: str, dtstart: datetime) -> dateutil_rrule.rrule:
        try:
            parsed = dateutil_rrule.rrulestr(rule, dtstart=dtstart)
        except (ValueError, TypeError) as exc:
            raise BadRequestException(f"Invalid recurrence rule: {exc}") from exc
        if not isinstance(parsed, dateutil_rrule.rrule):
            raise BadRequestException("Recurrence rule must be a single RRULE")
        return parsed

    async def list(self, user_id: uuid.UUID) -> list[Routine]:
        result = await self.db.scalars(
            select(Routine)
            .where(Routine.user_id == user_id)
            .order_by(Routine.created_at)
        )
        return list(result)

    async def create(self, user_id: uuid.UUID, data: RoutineCreate) -> Routine:
        # Validate the rule up front.
        self._parse_rrule(data.rrule, datetime.now(UTC))
        routine = Routine(
            user_id=user_id,
            title=data.title.strip(),
            rrule=data.rrule,
            domain_id=data.domain_id,
            standard_id=data.standard_id,
            default_energy=data.default_energy,
            default_context=data.default_context,
            default_duration_minutes=data.default_duration_minutes,
        )
        self.db.add(routine)
        await self.db.commit()
        await self.db.refresh(routine)
        return routine

    async def update(
        self, user_id: uuid.UUID, routine_id: uuid.UUID, data: RoutineUpdate
    ) -> Routine:
        routine = await self._get_owned(user_id, routine_id)
        payload = data.model_dump(exclude_unset=True)
        if "rrule" in payload and payload["rrule"]:
            self._parse_rrule(payload["rrule"], datetime.now(UTC))
        for key, value in payload.items():
            setattr(routine, key, value)
        await self.db.commit()
        await self.db.refresh(routine)
        return routine

    async def delete(self, user_id: uuid.UUID, routine_id: uuid.UUID) -> None:
        routine = await self._get_owned(user_id, routine_id)
        await self.db.delete(routine)
        await self.db.commit()

    async def generate(self, user_id: uuid.UUID) -> tuple[int, int]:
        """Materialize due instances for all active routines.

        Returns (generated, skipped_missed). Missed occurrences before the grace
        window are counted as skipped, never created.
        """
        routines = await self.list(user_id)
        today = datetime.now(UTC).date()
        horizon_end = today + timedelta(days=_GENERATION_HORIZON_DAYS)
        generated = 0
        skipped_missed = 0

        for routine in routines:
            if not routine.active:
                continue
            # Grace: start no earlier than today, regardless of last_generated_date.
            window_start = today
            if routine.last_generated_date and routine.last_generated_date >= today:
                window_start = routine.last_generated_date + timedelta(days=1)

            dtstart = datetime.combine(
                today - timedelta(days=370), datetime.min.time(), tzinfo=UTC
            )
            rule = self._parse_rrule(routine.rrule, dtstart)

            # Count missed (past) occurrences purely for transparency in the result.
            skipped_missed += sum(
                1
                for occ in rule.between(
                    datetime.combine(
                        today - timedelta(days=30),
                        datetime.min.time(),
                        tzinfo=UTC,
                    ),
                    datetime.combine(today, datetime.min.time(), tzinfo=UTC),
                    inc=False,
                )
            )

            occurrences = rule.between(
                datetime.combine(window_start, datetime.min.time(), tzinfo=UTC),
                datetime.combine(horizon_end, datetime.max.time(), tzinfo=UTC),
                inc=True,
            )
            for occ in occurrences:
                exists = await self._instance_exists(routine.id, occ)
                if exists:
                    continue
                self.db.add(
                    Item(
                        user_id=user_id,
                        title=routine.title,
                        status=STATUS_SCHEDULED,
                        kind=KIND_TASK,
                        domain_id=routine.domain_id,
                        standard_id=routine.standard_id,
                        routine_id=routine.id,
                        energy=routine.default_energy,
                        context=list(routine.default_context or []),
                        scheduled_at=occ,
                        duration_minutes=routine.default_duration_minutes,
                        source=SOURCE_MANUAL,
                    )
                )
                generated += 1
            routine.last_generated_date = horizon_end

        await self.db.commit()
        return generated, skipped_missed

    async def _instance_exists(
        self, routine_id: uuid.UUID, occ: datetime
    ) -> bool:
        existing = await self.db.scalar(
            select(Item.id).where(
                Item.routine_id == routine_id, Item.scheduled_at == occ
            )
        )
        return existing is not None
