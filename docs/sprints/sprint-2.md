# Sprint 2 — Auth + Tenancy

**Dates:** Mon 13 – Fri 24 Oct 2026 (run ahead of the roadmap's 2–13 Nov window)
**Goal:** A school can be onboarded end to end — Tafi staff create the school, invite its first admin, that admin
signs in — with roles and tenant scoping enforced by the API rather than by the UI.
**Closed:** Mon 13 Oct 2026 — see [Review & close-out](#review--close-out).

**Builds on:** `feature/sprint-1-foundation` (Sprint 1 is not merged into `main` yet; see
[`sprint-1.md`](sprint-1.md#review--close-out)).

## Objectives

1. Real accounts: sign in, sign out, invite, accept invite, reset password.
2. Roles: **platform admin** (Tafi staff), **school admin**, **driver** (the role exists; the driver screens are
   Sprint 4).
3. Tenancy: every operational row belongs to an organization, and the API — not the UI — enforces who may see it.
4. A platform admin console: create a school, invite its first admin, see the schools.
5. Staging-ready deployment configuration and a runbook.

## What the wireframes cover, and what they do not

The Sprint 1 deck has no sign-in, invitation or onboarding screen. It starts at
[`School portal · Today`](../ux/wireframes.md), already inside a school, with the school name and the signed-in
coordinator in the sidebar. So this sprint's screens are **new UI**, drawn to match the deck's tokens and shell —
they need a design review from Anne, not a redesign of the deck.

## Decisions this sprint makes

| Decision | Choice | Why |
|---|---|---|
| Password storage | **argon2** (`argon2-cffi`) | Current recommended default; no legacy constraints |
| Session | **JWT in an httpOnly cookie**, 12 hours, `SameSite=Lax`, `Secure` off local | Survives a page reload, unreadable to JavaScript, no token juggling in the client |
| CSRF | `SameSite=Lax` + a JSON-only API | Blocks cross-site form posts; a formal CSRF token is a hardening task, noted below |
| Refresh tokens | **Deferred** | One 12-hour session is enough for a pilot; see D-17 |
| Invite and reset delivery | The API stores a hashed, single-use, expiring token. **In `local` only** it also returns the link in the response, so the flow is testable before the notification worker exists (Sprint 5) | Nothing can send email or WhatsApp yet; the alternative is an untestable flow |
| Platform admins | `users.is_platform_admin` | They belong to Tafi, not to a tenant; keeps `memberships` about tenants only |
| Tenant roles | `memberships(user_id, organization_id, role)` with `school_admin` / `driver` | Generic tenancy per AGENTS.md — never hard-code "school" as the tenant root |

## Data model

```
users(id, email unique, name, password_hash, is_platform_admin, is_active, created_at, updated_at)
organizations(id, name, type, created_at, updated_at)            # exists
memberships(id, user_id -> users, organization_id -> organizations, role, created_at)
invitations(id, organization_id -> organizations, email, role, token_hash,
            expires_at, accepted_at, invited_by_user_id -> users, created_at)
password_reset_tokens(id, user_id -> users, token_hash, expires_at, used_at, created_at)
```

`memberships` is unique on `(user_id, organization_id)`.

## API contract

Base path `/api/v1`. Errors are FastAPI's `{"detail": "..."}` with a real status code.

### Auth

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/auth/sign-in` | `{email, password}` | `200 {user, memberships}` + `tafi_session` cookie; `401` on bad credentials |
| POST | `/auth/sign-out` | — | `204`, clears the cookie |
| GET | `/auth/me` | — | `200 {user, memberships}` or `401` |
| POST | `/auth/accept-invite` | `{token, name, password}` | `200 {user, memberships}` + cookie; `400` if the token is bad, used or expired |
| GET | `/auth/invitations/{token}` | — | `200 {email, organization_name, role}` or `400` — public, for the accept page |
| POST | `/auth/forgot-password` | `{email}` | `202` always, whether or not the address exists |
| POST | `/auth/reset-password` | `{token, password}` | `204`; `400` if the token is bad, used or expired |

Shapes:

```jsonc
// user
{ "id": "uuid", "email": "a@b.c", "name": "Anne W", "is_platform_admin": false }
// membership
{ "organization_id": "uuid", "organization_name": "Riverside Academy", "role": "school_admin" }
// sign-in response
{ "user": { ... }, "memberships": [ { ... } ] }
```

In `local`, the invite and forgot-password responses also carry `invite_url` / `reset_url`.

### Platform admin

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/organizations` | — | `200 [organization]` (list) |
| POST | `/organizations` | `{name, type}` | `201 organization` |
| POST | `/organizations/{id}/invitations` | `{email, role}` | `201 {id, email, role, expires_at}` (+ `invite_url` in local) |

### School

| Method | Path | Returns |
|---|---|---|
| GET | `/organization` | `200 organization` — the caller's own tenant; `403` if they have no membership |

All three platform routes require `is_platform_admin`. `/organization` requires a membership and returns only the
caller's own organization — the test for tenant isolation is that a school admin cannot read another school.

## Tasks

| ID | Task | Owner |
|---|---|---|
| S2-01 | Models, migration `0002`, password hashing, session cookie helpers | Herman — **Done** |
| S2-02 | Auth endpoints, role and tenant dependencies, tests | Herman — **Done** |
| S2-03 | Platform admin endpoints + `create-platform-admin` CLI for the first account | Herman — **Done** |
| S2-04 | Sign-in, accept-invite, forgot-password and reset-password pages; real session replaces the localStorage stub | Herman — **Done** |
| S2-05 | Platform admin console: schools list, create school, invite first admin | Herman — **Done** |
| S2-06 | Staging configuration (`docker-compose.prod.yml`, env list) and a deployment runbook | Herman — **Done, not deployed** |
| S2-07 | Review the new screens against the deck's tokens and shell; approve the copy | Anne — **carried** |
| S2-08 | Update every document that the code changed, and write the Sprint 2 delivery doc | Herman — **Done** |

## Definition of Done

- [x] `make up`, then the CLI creates a platform admin who can sign in.
- [x] The platform admin can create a school and invite its first admin; the invite token sets a name and password
      and the new admin ends up inside their school.
- [x] Password reset works end to end in `local`, and cannot be used twice or after expiry.
- [x] A school admin gets `403` on the platform routes, and cannot read another school's data — covered by tests.
- [x] Backend tests, ruff, mypy and the frontend lint/typecheck/build all pass.
- [x] Signing out ends the session, and a signed-out visitor is sent to sign in.
- [x] The delivery doc explains what to open and what to expect — [`docs/delivery/sprint-2.md`](../delivery/sprint-2.md).
- [x] Every document that names auth, roles or tenancy matches the code.

## Review & close-out

**Closed Mon 13 Oct 2026.** Seven of eight tasks are done; S2-07 (Anne's design review of the new screens) is the
only one carried, and it moves to [`homework/sprint-2.md`](../../homework/sprint-2.md).

### What Sprint 2 delivered

- **Accounts.** Sign in, sign out, invite, accept invite, forgot and reset password — verified end to end against
  the running stack, not only in tests.
- **Roles.** A platform admin flag on the user, and memberships with `school_admin` / `driver` inside an
  organization.
- **Tenancy.** Every protected route resolves the caller through the session cookie; the platform routes require
  `is_platform_admin`, and `GET /organization` returns only the caller's own tenant. Tests cover the refusal.
- **Onboarding.** A platform admin console at `/app/admin`: list schools, create one, invite its first admin, and
  see the invite link (in `local`).
- **A real session in the UI.** The Sprint 1 `localStorage` stub is gone; the protected side now follows an
  httpOnly cookie and `GET /api/v1/auth/me`.
- **Staging configuration.** `docker-compose.prod.yml`, a Caddyfile for TLS and same-origin API routing, and a
  runbook in [`../architecture/deployment.md`](../architecture/deployment.md).

### What was not finished

| Item | Left over | Owner | Where it goes |
|---|---|---|---|
| S2-07 | Anne has not reviewed the new screens (sign in, invite, reset, admin console) against the deck's tokens and shell | Anne | [`homework/sprint-2.md`](../../homework/sprint-2.md) |
| Hardening | Refresh tokens, a CSRF token, sign-in rate limiting, account lockout | Herman | Sprint 7, listed in the delivery doc |
| Deployment | Nothing is deployed: it needs the client's DigitalOcean account | Client | C-04 |

### Notes for the close-out

- **A session is a 12-hour JWT in an httpOnly cookie.** `SameSite=Lax` blocks cross-site form posts; a formal CSRF
  token is deliberately deferred to hardening, and the API is JSON-only.
- **Nothing can send email or WhatsApp yet**, so in `local` the invite and password-reset endpoints return the
  link in the response and the UI shows it. That is a development affordance gated on `app_env == "local"`; any
  other environment returns no link. Sprint 5 replaces it with the notification worker.
- **A driver can be invited but has nowhere to land yet.** The role is stored; the crew app is Sprint 4.

## Review

**Fri 24 Oct, 30 minutes — Anne, Herman and the client.** Walk the onboarding end to end on one screen, then the
school admin signing in. Confirm the Sprint 3 goal (school operations) and any scope change. The client-facing
walkthrough doubles as the demo owed from Sprint 1.

## Next sprint

**Sprint 3 (27 Oct – 7 Nov): School Operations.** Students, guardians (several per child, with consent), routes
and stops, vehicles, drivers, assignments and CSV import — the data every parent message depends on.

## Not in this sprint

- Driver sign-in screens (the role is stored; the app is Sprint 4).
- Refresh tokens, a formal CSRF token, rate limiting on sign-in, and account lockout — hardening for Sprint 7,
  listed in the delivery doc so they are not mistaken for done.
- Actually provisioning DigitalOcean staging: it needs the client's account. This sprint ships the configuration
  and the runbook; the run is a client action (C-04).
