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


def test_self_signup_defaults_on_in_local(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.delenv("ALLOW_SELF_SIGNUP", raising=False)

    assert Settings().self_signup_enabled is True


def test_self_signup_defaults_off_outside_local(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.delenv("ALLOW_SELF_SIGNUP", raising=False)

    assert Settings().self_signup_enabled is False


def test_self_signup_can_be_explicitly_enabled(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("ALLOW_SELF_SIGNUP", "true")

    assert Settings().self_signup_enabled is True
