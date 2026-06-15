"""Domain routes: CRUD, seasons, dashboard, standards, reflections, trends."""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, DbSession
from app.models.domain import Domain, Standard
from app.schemas.domain import (
    DashboardResponse,
    DomainCard,
    DomainCreate,
    DomainResponse,
    DomainUpdate,
    ReflectionCreate,
    ReflectionResponse,
    SeasonUpdate,
    StandardCreate,
    StandardResponse,
    StandardSignal,
    TrendPoint,
)
from app.schemas.response import ApiResponse
from app.services.domain_service import DomainService
from app.services.standard_service import StandardService

router = APIRouter()


def _to_card(card: dict[str, Any]) -> DomainCard:
    domain = cast(Domain, card["domain"])
    std_signals = cast(list[tuple[Standard, str, int]], card["standard_signals"])
    return DomainCard(
        domain=DomainResponse.model_validate(domain),
        signal=card["signal"],
        standard_signals=[
            StandardSignal(
                standard_id=std.id,
                text=std.text,
                signal=sig,  # type: ignore[arg-type]
                recent_count=count,
                target=std.target,
                cadence=std.cadence,  # type: ignore[arg-type]
            )
            for std, sig, count in std_signals
        ],
        needs_reflection=bool(card["needs_reflection"]),
        recent_wins=int(card["recent_wins"]),
    )


@router.get("")
async def list_domains(
    user: CurrentUser, db: DbSession
) -> ApiResponse[list[DomainResponse]]:
    """List domains with their standards."""
    domains = await DomainService(db).list(user.id)
    return ApiResponse(data=[DomainResponse.model_validate(d) for d in domains])


@router.get("/dashboard")
async def dashboard(
    user: CurrentUser, db: DbSession
) -> ApiResponse[DashboardResponse]:
    """The conscious-attention dashboard (focus + wins first)."""
    data = await DomainService(db).dashboard_data(user.id)
    cards = [_to_card(c) for c in cast(list[dict[str, Any]], data["cards"])]
    response = DashboardResponse(
        focus_priorities=cast(list[uuid.UUID], data["focus_priorities"]),
        recent_wins=int(cast(int, data["recent_wins"])),
        maintenance_domains=cast(list[uuid.UUID], data["maintenance_domains"]),
        paused_domains=cast(list[uuid.UUID], data["paused_domains"]),
        domains=cards,
    )
    return ApiResponse(data=response)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_domain(
    data: DomainCreate, user: CurrentUser, db: DbSession
) -> ApiResponse[DomainResponse]:
    """Create a life domain."""
    domain = await DomainService(db).create(user.id, data)
    return ApiResponse(data=DomainResponse.model_validate(domain))


@router.get("/{domain_id}")
async def get_domain(
    domain_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> ApiResponse[DomainResponse]:
    """Get a single domain."""
    domain = await DomainService(db).get(user.id, domain_id)
    return ApiResponse(data=DomainResponse.model_validate(domain))


@router.put("/{domain_id}")
async def update_domain(
    domain_id: uuid.UUID, data: DomainUpdate, user: CurrentUser, db: DbSession
) -> ApiResponse[DomainResponse]:
    """Update a domain."""
    domain = await DomainService(db).update(user.id, domain_id, data)
    return ApiResponse(data=DomainResponse.model_validate(domain))


@router.delete("/{domain_id}")
async def delete_domain(
    domain_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> ApiResponse[None]:
    """Delete a domain."""
    await DomainService(db).delete(user.id, domain_id)
    return ApiResponse(data=None)


@router.patch("/{domain_id}/season")
async def set_season(
    domain_id: uuid.UUID, data: SeasonUpdate, user: CurrentUser, db: DbSession
) -> ApiResponse[DomainResponse]:
    """Change a domain's season (a conscious choice, logged)."""
    domain = await DomainService(db).set_season(user.id, domain_id, data)
    return ApiResponse(data=DomainResponse.model_validate(domain))


# -- standards --------------------------------------------------------------
@router.post("/{domain_id}/standards", status_code=status.HTTP_201_CREATED)
async def create_standard(
    domain_id: uuid.UUID, data: StandardCreate, user: CurrentUser, db: DbSession
) -> ApiResponse[StandardResponse]:
    """Add a standard (Goodhart guard enforced for reflection-only domains)."""
    standard = await StandardService(db).create(user.id, domain_id, data)
    return ApiResponse(data=StandardResponse.model_validate(standard))


# -- reflections ------------------------------------------------------------
@router.post("/{domain_id}/reflections", status_code=status.HTTP_201_CREATED)
async def add_reflection(
    domain_id: uuid.UUID, data: ReflectionCreate, user: CurrentUser, db: DbSession
) -> ApiResponse[ReflectionResponse]:
    """Record a gentle 1-5 self-rating + note for the domain/standard."""
    entry = await DomainService(db).add_reflection(user.id, domain_id, data)
    return ApiResponse(data=ReflectionResponse.model_validate(entry))


@router.get("/{domain_id}/trend")
async def reflection_trend(
    domain_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> ApiResponse[list[TrendPoint]]:
    """Reflection trend over time (never a pass/fail verdict)."""
    points = await DomainService(db).trend(user.id, domain_id)
    return ApiResponse(data=points)
