"""Tests for the /health probe."""

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.routes import health as health_module


class _HealthyRedis:
    def ping(self) -> bool:
        return True


class _BrokenRedis:
    def ping(self) -> bool:
        raise RuntimeError("redis unavailable")


def test_health_ok(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(health_module, "get_redis", lambda: _HealthyRedis())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "redis": "ok"}


def test_health_reports_redis_failure(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(health_module, "get_redis", lambda: _BrokenRedis())

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "ok", "redis": "error"}
