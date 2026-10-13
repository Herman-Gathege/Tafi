# Architecture Decision

> Status: **DECIDED** (5 Oct 2026, D-08). The Sprint 1 technical questions are answered in
> [`spikes/sprint-1-spikes.md`](spikes/sprint-1-spikes.md) (8 Oct 2026).
> This is Option A from [`architecture-options.md`](architecture-options.md).

## Decision

Rebuild Tafi as a **modular monolith** on the team stack:

```text
Admin web app (React) ─┐
Driver web app (React) ─┼→ Caddy (TLS) → FastAPI API → PostgreSQL (SQLAlchemy + Alembic)
                        │                    │
                        │                    └→ Redis (queue, cache, rate limits)
                        │                          └→ Worker → WhatsApp Cloud API
Docker Compose · DigitalOcean (Linux) · Git
```

The Lovable prototype (TanStack Start + Supabase) is **not extended** (D-09). Its screens, flows and schema are
reference material.

## Why

- Both developers already run this stack in production on a comparable multi-tenant SaaS (tenancy, WhatsApp
  Cloud API templates, scheduled jobs, auth hardening), so the patterns transfer.
- Tafi's core value is background work: sending WhatsApp messages, evaluating "bus approaching", retries. That
  needs a worker.
- DigitalOcean with Docker is the target host.
- Full control of data, migrations and reporting.
- There is no pilot school yet, so the prototype's speed-to-first-user advantage is small.

## Components

| Component | Responsibility |
|---|---|
| Admin web app (React) | Tafi platform admin and school admin screens |
| Driver web app (React, mobile-first, installable) | Today's trips, check-in/out, location sharing |
| API (FastAPI) | Auth, tenancy, CRUD, trip events, location ingest, pricing |
| Worker | WhatsApp sends, ETA evaluation, scheduled jobs, retries |
| PostgreSQL | System of record |
| Redis | Queue, cache, rate limiting |
| Caddy | HTTPS and routing |
| WhatsApp Cloud API | Parent messages from the client's Meta Business account |

## Design rules

- **Tenancy:** every operational row belongs to an `organization` (type `school` now). Every query is scoped by
  organization in the API layer (D-10).
- **Notifications:** trip events write to an outbox table; the worker sends, logs status, and retries. Sends are
  idempotent (a child never gets two "boarded" messages for one trip).
- **Pricing:** plans and prices are database records editable by the platform admin (D-07).
- **Kenyan defaults:** E.164 phone numbers, `Africa/Nairobi` timezone, KES.
- **Migrations:** hand-written Alembic migrations, reviewed in PRs.

## Sprint 1 answers (T1-11 to T1-14)

| Question | Answer | Detail |
|---|---|---|
| Driver location while the screen is locked | **Not reliable in a browser.** Trip mode uses a wake lock and an explicit "keep this screen open" state; boarded/dropped off are taps and never depend on location | [T1-11](spikes/sprint-1-spikes.md#t1-11--driver-location-with-a-locked-screen) |
| Maps and ETA | **Leaflet + OSM tiles** for display, **LocationIQ** for geocoding, and "5 minutes away" **computed locally** from GPS fixes — no paid routing call in the hot path | [T1-12](spikes/sprint-1-spikes.md#t1-12--maps-and-eta) |
| Worker | **Celery + Celery Beat** (as built); swap cost is contained in `backend/app/worker/celery_app.py` | [T1-13](spikes/sprint-1-spikes.md#t1-13--worker-celery-vs-rq-vs-apscheduler) |
| PostgreSQL | **Container locally; DigitalOcean Managed PostgreSQL (~USD 15/month) for staging and production** | [T1-14](spikes/sprint-1-spikes.md#t1-14--postgresql-managed-or-container) |

## Repository layout (T1-06)

- `backend/` — FastAPI service: API, models, Alembic migrations, Celery worker, tests.
- `frontend/` — React + Vite web app; design tokens carried over from the prototype.
- `docker-compose.yml`, `Makefile`, `.env.example` — the local development stack (api, db, redis, worker, web).
- `.github/workflows/` — backend and frontend checks on every pull request.
- The client's Lovable prototype is preserved read-only at the tag **`prototype-lovable-2026-07`** and removed
  from the working tree (D-09, D-14).

CI runs on GitHub Actions for every branch push and every pull request, with `backend` and `frontend` as separate
workflows behind path filters. There is no image registry yet — the Sprint 1 stack builds locally, and the
registry decision belongs with the Sprint 2 staging deployment.

## What could change this decision

- Live location proves impossible from a web app → add a small native driver app (architecture otherwise unchanged).
- Scale beyond one VPS → separate worker host; still no microservices.
