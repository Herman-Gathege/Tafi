# Tafi API

FastAPI service for Tafi. Python 3.12, managed with [uv](https://docs.astral.sh/uv/).

## Run locally

```bash
uv sync --all-groups            # create .venv and install everything
uv run uvicorn app.main:app --reload
```

Configuration comes from the environment (see `.env.example` at the repository root).
Inside Docker Compose the API runs `alembic upgrade head` before starting uvicorn, so the
schema is always current.

## Tests

```bash
uv run pytest -q
```

Tests use an in-memory SQLite database and need no running services.

## Lint and type check

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app
```

## Migrations

Migrations are hand-written and reviewed in pull requests.

```bash
uv run alembic revision -m "Describe the change"   # start a new migration
uv run alembic upgrade head                         # apply
uv run alembic downgrade -1                         # roll back one
```

## Layout

| Path | Purpose |
|---|---|
| `app/main.py` | App factory and wiring |
| `app/core/` | Settings, logging, Redis client |
| `app/db/` | Engine, session, declarative base |
| `app/models/` | SQLAlchemy models (tenant root: `organization`) |
| `app/schemas/` | Pydantic contracts |
| `app/api/routes/` | HTTP endpoints (`/health`, `/api/v1/organizations`) |
| `app/worker/celery_app.py` | Celery app and placeholder task |
| `alembic/` | Migrations |
| `tests/` | Pytest suite |
