"""Settings must accept the comma-separated values we put in .env files."""

from app.core.config import Settings


def test_cors_origins_accepts_a_comma_separated_string(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173, https://app.tafi.co.ke")

    settings = Settings()

    assert settings.cors_origins == ["http://localhost:5173", "https://app.tafi.co.ke"]


def test_cors_origins_accepts_a_single_origin(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5180")

    settings = Settings()

    assert settings.cors_origins == ["http://localhost:5180"]
