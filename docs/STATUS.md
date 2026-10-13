# Tafi Status

_Last updated: 9 Oct 2026_

**Phase:** Sprint 1 closed (6–9 Oct 2026). **Sprint 2 — Auth + Tenancy is next.**

**Current objective:** Start Sprint 2 on accounts and tenancy, and clear the homework list.

## Where the product is

Tafi is a parent safety service for school transport: parents get WhatsApp updates when their child boards, when
the bus is approaching and when they are dropped off. Schools are the first customers. The product is being built
from scratch on the team stack; the client's Lovable prototype is archived at tag `prototype-lovable-2026-07`.

## Decided (see [`DECISIONS.md`](DECISIONS.md))

- The client is the product owner; Anne and Herman are the developers.
- Tafi is a **parent safety service**: parents get WhatsApp updates about their child's trip.
- **MVP 1 serves schools.** Other transport providers come later; the data model allows for them.
- Billing: **Tafi bills schools; schools bill parents** for transport.
- Platform pricing is **configurable by the client** without developers; KES 450/child/month is a placeholder.
- **Rebuild on the team stack** (FastAPI · React · PostgreSQL · Redis · Docker · DigitalOcean). Lovable is not used.
- Delivery window: **3 months, 4 max** → pilot-ready by end of January 2027.
- Parents use **WhatsApp only** in MVP 1 (D-12); the wireframes also draw a parent web dashboard, which stays an
  open question.

## Built so far

| Area | State |
|---|---|
| `backend/` | FastAPI with settings, JSON logging, `/health`, one Alembic migration and a Celery worker; ruff, mypy and 7 tests pass |
| `frontend/` | React + Vite + Tailwind on the prototype's design tokens, with a **public side** (`/`, `/wireframes`, `/signin`) and a **protected side** (`/app`) behind a development session |
| Local stack | `docker compose up` runs api + db + redis + worker + web; verified from a clean clone with an empty database |
| CI | GitHub Actions green on backend and frontend, on every branch push and pull request |
| Wireframes | 11 screens delivered by Anne, served at `/wireframes` and described in [`ux/wireframes.md`](ux/wireframes.md) |
| Spikes | T1-11 to T1-14 answered in [`architecture/spikes/sprint-1-spikes.md`](architecture/spikes/sprint-1-spikes.md) |

Nothing of MVP 1 beyond the placeholder organizations slice is implemented yet.

## Homework (what is left)

The full list is [`../homework/sprint-1.md`](../homework/sprint-1.md). In short:

- **Anne:** WhatsApp template copy (T1-03), the WhatsApp Cloud API spike (T1-15), the client scope review (T1-05),
  retiring stale assumption labels (T1-04), and two user conversations (C-03).
- **Herman:** open the pull request for the Sprint 1 branch, and get `annewaithaka/Tafi` made private (C-02).
- **Client:** Meta Business verification and a WhatsApp number, a pilot school introduction, and deleting the
  Lovable project (C-04) — plus two scope questions the wireframes raised: the Trips and Settings sections, and
  the parent Option B dashboard.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| `annewaithaka/Tafi` is still public | The client's code is readable by anyone | C-02: Anne changes visibility; the exposed keys stop working once the Lovable project is deleted (D-14) |
| WhatsApp Business verification and template approval take time | Parent messages blocked in Sprint 5 | Client starts verification now; templates submitted in Sprint 3 |
| School calendar: Term 3 closes late Oct/early Nov | No one to interview or pilot with over the holidays | User conversations still owed (C-03); pilot in Term 1 2027 |
| "Bus approaching" needs live location from a driver's phone, and browsers pause location when the screen locks | The core parent message is unreliable | Answered in T1-11: wake-lock trip mode with a graceful fallback; confirm with drivers in C-03 |
| No pilot school yet | Nothing to validate against | Client introduction is C-04 |
| Children's personal data (Kenya Data Protection Act 2019) | Legal and trust risk | Consent is designed into the wireframes; privacy checklist is MVP-22 |
| 3–4 month window is tight | Scope creep delays the pilot | 2-week sprints, strict MVP 1 scope, billing can move after the pilot |

## Next

Clear the homework list → Sprint 2 (auth + tenancy, staging on DigitalOcean) → demo the wireframes and the
wireframe gallery to the client.
