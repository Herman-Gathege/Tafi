# Tafi Agent Instructions

## Project Context

- Tafi is **client work**. The client owns product decisions; Anne Waithaka and Herman Gathege are the developers.
- The code currently in this repository is a **prototype** the client generated with Lovable. It is reference
  material only. **We do not use Lovable**, and the product is being rebuilt on the team stack (see `docs/DECISIONS.md`).
- Product: a **parent safety service for transport**. Parents get WhatsApp updates (boarded, dropped off, bus
  approaching). Schools pay for it first (MVP 1); other transport providers follow.

## Project Principle

Do not jump directly into implementation. Follow:

Discovery → Research → Product decision → UX/UI → Architecture → Implementation → Testing → Deployment

## Current Phase

**Sprint 1 — UX + Foundation (19–30 Oct 2026).** Sprint 0 closed on 6 Oct 2026; its four carry-over items
(C-01 to C-04) are in [`docs/sprints/sprint-0.md`](docs/sprints/sprint-0.md#review--close-out) and the current
plan is [`docs/sprints/sprint-1.md`](docs/sprints/sprint-1.md). Therefore:

- do not implement MVP features unless explicitly instructed
- work to the Sprint 1 plan; security hygiene fixes stay allowed (repo visibility, secrets) — see `docs/DECISIONS.md` D-02
- do not refactor or extend the prototype; it will be replaced
- use documentation to capture decisions
- ask for clarification where product requirements are ambiguous
- distinguish **FACT / OBSERVATION / ASSUMPTION / UNKNOWN**
- keep documentation concise

## Technical Direction (decided — D-08)

React · FastAPI · PostgreSQL · SQLAlchemy · Alembic · Redis · background worker · Docker · Docker Compose ·
Caddy/Nginx · DigitalOcean (Linux) · Git

- Do not add Supabase, Lovable or TanStack Start code to the new build.
- Prototype code is read-only reference for screens, flows and the data model.

## Architecture Principles

- **Modular monolith.** No microservices without a demonstrated requirement.
- **Generic tenancy.** The tenant is an `organization` with a type (`school` in MVP 1; transport operators later).
  Never hard-code "school" as the tenant root.
- **Notifications are asynchronous.** WhatsApp sends go through the worker queue, are logged and retried;
  request handlers never call WhatsApp directly.
- **Commercial settings are data.** Platform pricing and plans are editable by the Tafi platform admin, never
  hard-coded.
- **Kenyan defaults.** Phone numbers stored in E.164 (`+2547…`); schedules in `Africa/Nairobi`; currency KES.

## Development Principles

- mobile-first
- accessibility-conscious
- responsive
- reusable components
- clear API boundaries
- typed contracts
- database migrations (hand-written Alembic)
- automated tests
- environment-based configuration
- secure secrets
- structured logging
- health checks
- production-ready Docker setup

## Documentation Principle

Documentation must be short, useful, current, decision-oriented, and owner-readable.
Do not create documentation for the sake of documentation. See `docs/README.md`.

## Git Workflow

- Branch from `main`: `feature/<name>` · `fix/<name>` · `research/<name>` · `codex/<name>`.
- Do not commit directly to `main`. Every meaningful change goes through a PR reviewed by the other developer
  (see `docs/CONTRIBUTING.md`).
- Commit messages: a short imperative sentence in sentence case, no prefixes or scope tags
  (e.g. `Add guardian phone validation`).
- Never commit `.env` files or secrets.

## Sprint Discipline

Every sprint should have: **Goal · Tasks · Deliverables · Definition of Done · Review · Next sprint.**
