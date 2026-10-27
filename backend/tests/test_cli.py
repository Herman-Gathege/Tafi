"""Operational commands (Sprint 4 review, fix 6)."""

from types import SimpleNamespace

import pytest

from app import cli


@pytest.mark.parametrize("environment", ["staging", "production", ""])
def test_seed_demo_refuses_to_run_outside_local(
    monkeypatch: pytest.MonkeyPatch, environment: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Its passwords are in the repository, so it must never touch a real server."""
    monkeypatch.setattr(cli, "get_settings", lambda: SimpleNamespace(app_env=environment))

    with pytest.raises(cli.NotLocalError):
        cli.seed_demo()

    assert cli.main(["seed-demo"]) == 1
    assert "only runs with APP_ENV=local" in capsys.readouterr().out
