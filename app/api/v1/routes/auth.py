"""Auth and account-recovery routes."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.config import settings
from app.core.dependencies import DbSession  # noqa: TC001
from app.schemas.auth import (
    AuthLogin,
    AuthSetup,
    AuthToken,
    RecoveryRequest,
    RecoveryReset,
)
from app.schemas.response import ApiResponse
from app.services.auth_service import AuthService
from app.services.seed_service import SeedService

router = APIRouter()


@router.post("/setup", status_code=status.HTTP_201_CREATED)
async def setup(data: AuthSetup, db: DbSession) -> ApiResponse[AuthToken]:
    """Create the first account and seed default domains."""
    token, user = await AuthService(db).setup(data)
    await SeedService(db).seed_defaults(user.id)
    return ApiResponse(data=AuthToken(access_token=token))


@router.post("/login")
async def login(data: AuthLogin, db: DbSession) -> ApiResponse[AuthToken]:
    """Log in and receive a JWT."""
    token = await AuthService(db).login(data)
    return ApiResponse(data=AuthToken(access_token=token))


@router.post("/recovery/request")
async def request_recovery(
    data: RecoveryRequest, db: DbSession
) -> ApiResponse[dict[str, bool | str | None]]:
    """Request a recovery code. Always returns a generic payload.

    EmailService emails the code when SMTP is configured, or logs it in local.
    In local/dev the plaintext code is also returned as ``dev_code`` for testing.
    """
    code = await AuthService(db).request_recovery(data.username)
    payload: dict[str, bool | str | None] = {"sent": code is not None}
    if settings.environment == "local" and code is not None:
        payload["dev_code"] = code
    return ApiResponse(data=payload)


@router.post("/recovery/reset")
async def reset_password(
    data: RecoveryReset, db: DbSession
) -> ApiResponse[AuthToken]:
    """Reset the password using a valid recovery code."""
    token = await AuthService(db).reset_password(data)
    return ApiResponse(data=AuthToken(access_token=token))
