# Tafi Status

_Last updated: 13 Oct 2026_

**Phase:** Sprint 2 closed (13 Oct 2026). **Sprint 3 — School Operations is next.**

**Current objective:** Build the school's data — students, guardians, routes and stops, vehicles, drivers — and
clear the homework list.

## Where the product is

Tafi is a parent safety service for school transport: parents get WhatsApp updates when their child boards, when
the bus is approaching and when they are dropped off. Schools are the first customers. The product is built from
scratch on the team stack; the client's Lovable prototype is archived at tag `prototype-lovable-2026-07`.

**You can open the app today.** Walk through it with [`delivery/sprint-2.md`](delivery/sprint-2.md).

## Decided (see [`DECISIONS.md`](DECISIONS.md))

- The client is the product owner; Anne and Herman are the developers.
- Tafi is a **parent safety service**: parents get WhatsApp updates about their child's trip.
- **MVP 1 serves schools.** Other transport providers come later; the data model allows for them.
- Billing: **Tafi bills schools; schools bill parents** for transport.
- Platform pricing is **configurable by the client** without developers; KES 450/child/month is a placeholder.
- **Rebuild on the team stack** (FastAPI · React · PostgreSQL · Redis · Docker · DigitalOcean). Lovable is not used.
- Delivery window: **3 months, 4 max** → pilot-ready by end of January 2027.
- Parents use **WhatsApp only** in MVP 1 (D-12); the wireframes also draw a parent web dashboard, which is still
  an open question.
- A session is a **12-hour JWT in an httpOnly cookie** (D-17); invite and reset links are returned in the API
  response **in `local` only** until the notification worker exists (D-18).

## Built so far

| Area | State |
|---|---|
| Accounts | Sign in, sign out, invite, accept invite, forgot and reset password — verified against the running stack |
| Roles | `is_platform_admin` on the user; `school_admin` and `driver` in memberships |
| Tenancy | Protected routes resolve the caller's organization; platform routes refuse school admins with `403` |
| Onboarding | `/app/admin`: list schools, create a school, invite its first admin |
| `backend/` | FastAPI with settings, JSON logging, `/health`, two Alembic migrations, Celery worker; ruff, mypy and 24 tests pass |
| `frontend/` | React + Vite + Tailwind on the prototype's design tokens, with a public side, a protected side and real sessions |
| Local stack | `docker compose up` runs api + db + redis + worker + web |
| CI | GitHub Actions green on backend and frontend, on every branch push and pull request |
| Wireframes | 11 screens, served at `/wireframes` and described in [`ux/wireframes.md`](ux/wireframes.md) |
| Spikes | T1-11 to T1-14 answered in [`architecture/spikes/sprint-1-spikes.md`](architecture/spikes/sprint-1-spikes.md) |

Nothing of Sprint 3 is built yet, and nothing is deployed.

## Homework (what is left)

The live list is in [`../homework/`](../homework/README.md). In short:

- **Anne:** the design review of the new screens (S2-07); WhatsApp template copy (T1-03); the WhatsApp Cloud API
  spike (T1-15); the client scope review (T1-05); retiring stale assumption labels (T1-04); two user
  conversations (C-03).
- **Herman:** open the pull requests for the Sprint 1 and Sprint 2 branches; hardening (refresh tokens, CSRF,
  sign-in rate limiting); get `annewaithaka/Tafi` made private (C-02).
- **Client:** Meta Business verification and a WhatsApp number, a pilot school introduction, deleting the Lovable
  project (C-04), a DigitalOcean account for staging, and answers to the two scope questions the wireframes raised.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| `annewaithaka/Tafi` is still public | The client's code is readable by anyone | C-02: Anne changes visibility; the exposed keys stop working once the Lovable project is deleted (D-14) |
| Nothing is deployed | The client cannot see progress without running Docker | Staging configuration and a runbook are ready; it needs the client's DigitalOcean account |
| No email or WhatsApp delivery | Invites and password resets only work by copying a link | Local-only links (D-18); real delivery in Sprint 5 |
| Sprint 1 and Sprint 2 branches are unmerged | Nothing has been reviewed, and the stack grows | Open the pull requests; PR #4 (Sprint 0) is still open too |
| School calendar: Term 3 closes late Oct/early Nov | No one to interview or pilot with over the holidays | User conversations still owed (C-03); pilot in Term 1 2027 |
| Children's personal data (Kenya Data Protection Act 2019) | Legal and trust risk | Consent is designed into the wireframes; privacy checklist is MVP-22 |

## Next

Sprint 3 (school operations: students, guardians with consent, routes and stops, vehicles, drivers, assignments,
CSV import) → clear the homework list → deploy staging once the client provides an account.
