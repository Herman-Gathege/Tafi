"""Application settings, read from the environment (12-factor)."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    Values come from environment variables (or a local `.env` file in development).
    Never commit real values: see `.env.example` at the repository root.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: str = "local"
    log_level: str = "INFO"
    # Long enough to satisfy HMAC-SHA256 offline; replace it in every real environment.
    secret_key: str = "local-development-secret-change-me-in-every-other-environment"
    database_url: str = "sqlite+pysqlite:///:memory:"
    redis_url: str = "redis://localhost:6379/0"

    # Where the app is served from — used to build invite and reset links.
    app_public_url: str = "http://localhost:5173"

    # Sessions.
    session_cookie_name: str = "tafi_session"
    session_ttl_hours: int = 12
    session_cookie_secure: bool = False

    # None follows APP_ENV: enabled locally, disabled everywhere else.
    allow_self_signup: bool | None = None
    auth_sign_in_limit: int = Field(default=20, ge=1)
    auth_signup_limit: int = Field(default=5, ge=1)
    auth_rate_window_seconds: int = Field(default=60, ge=1)

    # Invitations and password resets.
    invite_ttl_days: int = 7
    reset_ttl_hours: int = 2
    # NoDecode: the value arrives as a comma-separated string from the environment
    # (e.g. "http://localhost:5173,https://app.tafi.co.ke"); without it
    # pydantic-settings tries to JSON-decode the field before the validator runs.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Accept a comma-separated string (as in `.env`) or a list."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def self_signup_enabled(self) -> bool:
        """Signup is opt-in outside local development."""
        if self.allow_self_signup is not None:
            return self.allow_self_signup
        return self.app_env == "local"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings()
