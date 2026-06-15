"""JWT tokens, password/recovery hashing, and at-rest encryption helpers."""

from __future__ import annotations

import base64
import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import AppException

# bcrypt operates on the first 72 bytes; truncate explicitly to stay deterministic.
_BCRYPT_MAX_BYTES = 72


def _pw_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


# ---------------------------------------------------------------------------
# Password hashing (bcrypt directly - avoids passlib/bcrypt version drift)
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(_pw_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(_pw_bytes(plain), hashed.encode("utf-8"))
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
def create_access_token(user_id: uuid.UUID) -> str:
    """Create a signed JWT access token for the given user id."""
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_expiry_days)
    payload: dict[str, Any] = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> uuid.UUID:
    """Decode a JWT and return the user id. Raises AppException(401) if invalid."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        sub = payload.get("sub")
        if not isinstance(sub, str):
            raise AppException(401, "Invalid authentication token")
        return uuid.UUID(sub)
    except (JWTError, ValueError) as exc:
        raise AppException(401, "Invalid authentication token") from exc


# ---------------------------------------------------------------------------
# Recovery codes (hashed, never stored plain)
# ---------------------------------------------------------------------------
def generate_recovery_code() -> str:
    """Generate a human-friendly recovery code."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_recovery_code(code: str) -> str:
    """Hash a recovery code for storage (SHA-256 is sufficient for short-lived codes)."""
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def verify_recovery_code(code: str, hashed: str) -> bool:
    """Constant-time comparison of a recovery code against its stored hash."""
    return secrets.compare_digest(hash_recovery_code(code), hashed)


# ---------------------------------------------------------------------------
# At-rest encryption for OAuth tokens (Fernet)
# ---------------------------------------------------------------------------
def _fernet() -> Fernet:
    if not settings.encryption_key:
        raise AppException(
            500, "ENCRYPTION_KEY is not configured; cannot store external tokens"
        )
    # Accept either a valid Fernet key or any string (derive a key from it).
    key = settings.encryption_key
    try:
        return Fernet(key)
    except (ValueError, TypeError):
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a secret (e.g. OAuth token) for storage at rest."""
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt a secret stored at rest."""
    try:
        return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise AppException(500, "Failed to decrypt stored secret") from exc
