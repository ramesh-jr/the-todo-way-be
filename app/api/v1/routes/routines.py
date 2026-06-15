"""Routine routes, including grace-respecting instance generation."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.response import ApiResponse
from app.schemas.routine import (
    GenerateResult,
    RoutineCreate,
    RoutineResponse,
    RoutineUpdate,
)
from app.services.routine_service import RoutineService

router = APIRouter()


@router.get("")
async def list_routines(
    user: CurrentUser, db: DbSession
) -> ApiResponse[list[RoutineResponse]]:
    """List all routines."""
    routines = await RoutineService(db).list(user.id)
    return ApiResponse(data=[RoutineResponse.model_validate(r) for r in routines])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_routine(
    data: RoutineCreate, user: CurrentUser, db: DbSession
) -> ApiResponse[RoutineResponse]:
    """Create a recurring generator."""
    routine = await RoutineService(db).create(user.id, data)
    return ApiResponse(data=RoutineResponse.model_validate(routine))


@router.post("/generate")
async def generate(
    user: CurrentUser, db: DbSession
) -> ApiResponse[GenerateResult]:
    """Materialize due instances (grace: missed occurrences are skipped, not stacked)."""
    generated, skipped = await RoutineService(db).generate(user.id)
    return ApiResponse(
        data=GenerateResult(generated=generated, skipped_missed=skipped)
    )


@router.put("/{routine_id}")
async def update_routine(
    routine_id: uuid.UUID, data: RoutineUpdate, user: CurrentUser, db: DbSession
) -> ApiResponse[RoutineResponse]:
    """Update a routine."""
    routine = await RoutineService(db).update(user.id, routine_id, data)
    return ApiResponse(data=RoutineResponse.model_validate(routine))


@router.delete("/{routine_id}")
async def delete_routine(
    routine_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> ApiResponse[None]:
    """Delete a routine."""
    await RoutineService(db).delete(user.id, routine_id)
    return ApiResponse(data=None)
