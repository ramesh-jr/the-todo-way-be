"""Standard business logic, including the Goodhart guard."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.domain import STANDARD_COUNTABLE, STANDARD_REFLECTION, Domain, Standard
from app.schemas.domain import StandardCreate, StandardUpdate


class StandardService:
    """CRUD for standards. Enforces that reflection-only domains stay reflection-only."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_domain(self, user_id: uuid.UUID, domain_id: uuid.UUID) -> Domain:
        domain = await self.db.scalar(
            select(Domain).where(Domain.id == domain_id, Domain.user_id == user_id)
        )
        if domain is None:
            raise NotFoundException("Domain")
        return domain

    async def _get_owned(
        self, user_id: uuid.UUID, standard_id: uuid.UUID
    ) -> tuple[Standard, Domain]:
        standard = await self.db.scalar(
            select(Standard).where(Standard.id == standard_id)
        )
        if standard is None:
            raise NotFoundException("Standard")
        domain = await self._get_domain(user_id, standard.domain_id)
        return standard, domain

    async def create(
        self, user_id: uuid.UUID, domain_id: uuid.UUID, data: StandardCreate
    ) -> Standard:
        domain = await self._get_domain(user_id, domain_id)
        kind = data.kind
        # Goodhart guard: relationships / intrinsic things are never counted.
        if domain.reflection_only and kind == STANDARD_COUNTABLE:
            raise BadRequestException(
                "This domain is reflection-only; standards here cannot be counted. "
                "Relationships are not measured by checkboxes."
            )
        if kind == STANDARD_COUNTABLE and data.target is None:
            raise BadRequestException("Countable standards require a target")
        standard = Standard(
            domain_id=domain.id,
            text=data.text.strip(),
            kind=kind,
            cadence=data.cadence if kind == STANDARD_COUNTABLE else None,
            target=data.target if kind == STANDARD_COUNTABLE else None,
            sort_order=data.sort_order,
        )
        self.db.add(standard)
        await self.db.commit()
        await self.db.refresh(standard)
        return standard

    async def update(
        self, user_id: uuid.UUID, standard_id: uuid.UUID, data: StandardUpdate
    ) -> Standard:
        standard, _ = await self._get_owned(user_id, standard_id)
        payload = data.model_dump(exclude_unset=True)
        # Reflection standards never gain a cadence/target.
        if standard.kind == STANDARD_REFLECTION:
            payload.pop("cadence", None)
            payload.pop("target", None)
        for key, value in payload.items():
            setattr(standard, key, value)
        await self.db.commit()
        await self.db.refresh(standard)
        return standard

    async def delete(self, user_id: uuid.UUID, standard_id: uuid.UUID) -> None:
        standard, _ = await self._get_owned(user_id, standard_id)
        await self.db.delete(standard)
        await self.db.commit()
