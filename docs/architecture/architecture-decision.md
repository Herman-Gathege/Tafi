# Architecture Decision

> Status: **DECIDED** (5 Oct 2026, D-08). "Open technical questions" are settled in Sprint 1.
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

## Open technical questions (Sprint 1 spikes)

1. **Driver location:** can a browser web app keep sending location with the screen locked on Android and iPhone?
   If not: a "keep screen on" trip mode, or a thin native wrapper later.
2. **Maps and ETA:** Google Maps vs an OpenStreetMap-based option (cost); how to calculate "5 minutes away".
3. **Worker:** Celery vs RQ vs APScheduler plus a queue.
4. **PostgreSQL:** DigitalOcean Managed Database vs a container with a persistent volume.
5. **Repo layout:** `backend/` + `frontend/` in this repo, with the prototype preserved on a tag or archive branch.
6. **CI and registry:** which runner and image registry.

## What could change this decision

- Live location proves impossible from a web app → add a small native driver app (architecture otherwise unchanged).
- Scale beyond one VPS → separate worker host; still no microservices.
