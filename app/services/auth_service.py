"""Authentication and account-recovery business logic."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    UnauthorizedException,
)
from app.core.security import (
    create_access_token,
    generate_recovery_code,
    hash_password,
    hash_recovery_code,
    verify_password,
    verify_recovery_code,
)
from app.models.user import User
from app.schemas.auth import AuthLogin, AuthSetup, RecoveryReset


class AuthService:
    """Single-user auth: setup, login, and recovery."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _user_count(self) -> int:
        count = await self.db.scalar(select(func.count()).select_from(User))
        return int(count or 0)

    async def setup(self, data: AuthSetup) -> tuple[str, User]:
        """Create the first (and only) user. 409 if a user already exists."""
        if await self._user_count() > 0:
            raise ConflictException("An account already exists")
        user = User(
            username=data.username,
            password_hash=hash_password(data.password),
            recovery_email=data.recovery_email,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return create_access_token(user.id), user

    async def login(self, data: AuthLogin) -> str:
        """Verify credentials and return a JWT."""
        user = await self.db.scalar(
            select(User).where(User.username == data.username)
        )
        if user is None or not verify_password(data.password, user.password_hash):
            raise UnauthorizedException("Invalid username or password")
        return create_access_token(user.id)

    async def request_recovery(self, username: str) -> str | None:
        """Issue a recovery code, deliver via EmailService, return the plaintext code.

        Returns None if there is no recovery email on file; callers should not reveal
        whether an account/email exists. The plaintext code is returned so local/dev
        routes can surface it for testing; production should only email it.
        """
        from app.services.email_service import EmailService

        user = await self.db.scalar(select(User).where(User.username == username))
        if user is None or not user.recovery_email:
            return None
        code = generate_recovery_code()
        user.recovery_code_hash = hash_recovery_code(code)
        user.recovery_code_expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.recovery_code_ttl_minutes
        )
        await self.db.commit()
        EmailService().send_recovery_code(
            to=user.recovery_email, username=user.username, code=code
        )
        return code

    async def reset_password(self, data: RecoveryReset) -> str:
        """Reset the password using a valid, unexpired recovery code."""
        user = await self.db.scalar(
            select(User).where(User.username == data.username)
        )
        if (
            user is None
            or not user.recovery_code_hash
            or not user.recovery_code_expires_at
        ):
            raise BadRequestException("Invalid or expired recovery code")
        expires = user.recovery_code_expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires < datetime.now(UTC):
            raise BadRequestException("Invalid or expired recovery code")
        if not verify_recovery_code(data.code, user.recovery_code_hash):
            raise BadRequestException("Invalid or expired recovery code")
        user.password_hash = hash_password(data.new_password)
        user.recovery_code_hash = None
        user.recovery_code_expires_at = None
        await self.db.commit()
        return create_access_token(user.id)
