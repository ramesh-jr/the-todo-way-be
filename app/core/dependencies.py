"""FastAPI dependency injection (get_db, get_current_user)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import verify_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    """Resolve the authenticated user from the bearer token."""
    if not token:
        raise AppException(401, "Not authenticated")
    user_id = verify_token(token)
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise AppException(401, "User not found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
