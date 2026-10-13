# Tafi

A parent safety service for transport in Kenya. Parents get WhatsApp updates when their child boards, is dropped
off, or the bus is approaching. Schools are the first customers; other transport providers follow.

## Status

**Sprint 1 closed 9 Oct 2026; Sprint 2 — Auth + Tenancy is next.** See [`docs/STATUS.md`](docs/STATUS.md) and
[`docs/sprints/sprint-1.md`](docs/sprints/sprint-1.md). What is still open is tracked in
[`homework/`](homework/README.md).

## Repository contents

- `backend/` — FastAPI service (API, migrations, worker).
- `frontend/` — React web app for the school and platform admin experiences.
- `docs/` — planning, decisions, research and sprints. Start at [`docs/README.md`](docs/README.md).
- `homework/` — what each sprint left behind, with owners and next actions.
- `docker-compose.yml`, `Makefile`, `.env.example` — the local development stack.

The client's original Lovable prototype has been removed from the working tree. It is preserved read-only at the
tag **`prototype-lovable-2026-07`** (`git show prototype-lovable-2026-07:src/routes/index.tsx`) and is reference
material for screens, flows and the data model only.

## Local development

Requires Docker with Compose, and Node 22.12+ if you run the web app outside Docker.

```sh
make up      # build and start api + db + redis + worker + web
make logs    # follow the logs
make down    # stop everything
```

Then:

| What | URL |
|---|---|
| Landing page (public) | <http://localhost:5173> |
| MVP 1 wireframes, with a jump-to-screen list | <http://localhost:5173/wireframes> |
| The school portal (protected; use "Enter the demo") | <http://localhost:5173/signin> |
| API health | <http://localhost:8000/health> |
| API docs | <http://localhost:8000/docs> |

`make setup` copies `.env.example` to `.env`. If ports 8000, 5173, 5432 or 6379 are already in use on your
machine, change `API_PORT`, `WEB_PORT`, `POSTGRES_HOST_PORT` and `REDIS_HOST_PORT` in `.env` first. Other
commands: `make migrate`, `make psql`, `make test`, `make lint`, `make format`.

## Planned stack

React · FastAPI · PostgreSQL · Redis · background worker · Docker Compose · DigitalOcean.
Details: [`docs/architecture/architecture-decision.md`](docs/architecture/architecture-decision.md).

## Contributing

See [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) and [`AGENTS.md`](AGENTS.md).
