# Deployment Foundation

> Target model for when we build. **Do not build this yet.** Docker-first, DigitalOcean VPS.

## Conceptual topology

```text
Internet
  → Domain (DNS)
    → Caddy/Nginx (TLS, reverse proxy)
      → Frontend (static React build / web server)
      → FastAPI (API)
        → PostgreSQL (persistent volume)
        → Redis
          → Background worker (Celery/RQ)
```

## Docker Compose (services)

| Service | Role | Notes |
|---|---|---|
| `web` | Serve frontend build | Static assets via Caddy/Nginx |
| `api` | FastAPI app | Uvicorn/Gunicorn behind proxy |
| `db` | PostgreSQL | Named volume for persistence |
| `redis` | Cache + queue | Ephemeral |
| `worker` | Celery/RQ | Notifications, scheduled jobs |
| `proxy` | Caddy/Nginx | HTTPS + routing (may replace `web`) |

## Operational requirements

- **Persistent PostgreSQL volume** — never lose data on redeploy.
- **Environment variables & secrets** — via `.env`/secret store, **never committed**.
- **Backups** — scheduled `pg_dump` off-host + retention policy; test restores.
- **Health checks** — for `api`, `db`, `redis`; use `depends_on: condition: service_healthy`.
- **Logging** — structured JSON logs; container log rotation; centralise if needed.
- **HTTPS** — automatic certs (Caddy or Certbot + Nginx).
- **Rollback** — tag images per release; keep previous image to re-deploy.

## Deployment process (outline)

1. Build & tag images in CI (or locally).
2. Push to registry.
3. On the host: `docker compose pull` → `compose up -d`.
4. Run migrations (Alembic) as a one-shot job.
5. Verify health checks + smoke test.

## Rollback strategy (outline)

- Keep the last known-good image tag; redeploy it.
- Migrations must be **backwards-compatible** where possible; keep a down path.

## Open questions

- **Settled (Sprint 1, T1-14):** container on the VPS for local development; **DigitalOcean Managed PostgreSQL**
  for staging and production.
- **Settled (Sprint 2):** one VPS running `docker-compose.prod.yml`; Caddy terminates TLS and routes `/api/*` to
  the API, everything else to the static web image.
- Still open: which container registry, and whether the worker eventually gets its own host.

## Staging runbook (Sprint 2)

Configuration lives in [`../../docker-compose.prod.yml`](../../docker-compose.prod.yml) and
[`../../deploy/Caddyfile`](../../deploy/Caddyfile). It has not been run anywhere yet: staging needs the client's
DigitalOcean account (C-04).

1. **Provision.** One DigitalOcean droplet (Ubuntu LTS, 2 GB is enough for a pilot) and a managed PostgreSQL
   cluster on the same private network. Point the domain's A record at the droplet.
2. **Install.** Docker Engine and the Compose plugin. Clone the repository at the branch to deploy.
3. **Write `.env.production`** next to `docker-compose.prod.yml` — never in git:

   ```sh
   APP_ENV=staging
   SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(48))">
   DATABASE_URL=postgresql+psycopg://<user>:<password>@<host>:25060/<db>?sslmode=require
   REDIS_URL=redis://redis:6379/0
   CORS_ORIGINS=https://<domain>
   APP_PUBLIC_URL=https://<domain>
   ```

   In this shape Caddy serves the app and the API on one origin, so the browser makes no cross-origin requests and
   `CORS_ORIGINS` only matters if something else calls the API.
4. **Start.**

   ```sh
   DOMAIN=<domain> VITE_API_BASE_URL=https://<domain> \
     docker compose -f docker-compose.prod.yml up -d --build
   docker compose -f docker-compose.prod.yml exec api alembic upgrade head
   docker compose -f docker-compose.prod.yml exec api \
     python -m app.cli create-platform-admin --email <you> --password <a long one>
   ```

   `VITE_API_BASE_URL` is baked into the web image at build time — rebuild the `web` service when the domain
   changes.
5. **Check.** `https://<domain>/health` returns `{"status":"ok",...}`, the certificate is valid, and signing in at
   `https://<domain>/signin` works.
6. **Routine.** Nightly `pg_dump` off-host with a retention policy, and a restore test before the pilot starts.
   The managed cluster's own backups are the first line; this is the second.

Because `APP_ENV` is not `local`, the invite and reset endpoints return no links in staging (D-18) — until Sprint 5
delivers notifications, onboard people by generating a link in a local run against staging's database, or hold
staging onboarding until the notification work lands.
