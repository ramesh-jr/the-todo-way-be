"""Auth and account-recovery schemas."""

from pydantic import BaseModel, Field


class AuthSetup(BaseModel):
    """First-time account creation."""

    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    recovery_email: str | None = Field(None, max_length=320)


class AuthLogin(BaseModel):
    """Login credentials."""

    username: str
    password: str


class AuthToken(BaseModel):
    """Issued JWT."""

    access_token: str
    token_type: str = "bearer"


class RecoveryRequest(BaseModel):
    """Request a recovery code be sent to the recovery email."""

    username: str


class RecoveryReset(BaseModel):
    """Reset the password using a recovery code."""

    username: str
    code: str
    new_password: str = Field(..., min_length=6)
