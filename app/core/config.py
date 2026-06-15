"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings loaded from environment variables / .env file."""

    # Core
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_days: int = 7
    environment: str = "local"  # local | staging | production
    cors_origins: list[str] = ["http://localhost:5173"]

    # Public base URL of the API (used for OAuth redirect URIs).
    app_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:5173"

    # Encryption key for OAuth tokens at rest (Fernet, urlsafe base64, 32 bytes).
    # Optional in local dev; required before connecting external calendars.
    encryption_key: str | None = None

    # Web Push (VAPID). Optional until push is configured.
    vapid_public_key: str | None = None
    vapid_private_key: str | None = None
    vapid_subject: str = "mailto:admin@example.com"

    # Calendar OAuth (Google / Microsoft Graph). Optional until configured.
    google_client_id: str | None = None
    google_client_secret: str | None = None
    ms_client_id: str | None = None
    ms_client_secret: str | None = None

    # Account recovery: how long a recovery code is valid (minutes).
    recovery_code_ttl_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
