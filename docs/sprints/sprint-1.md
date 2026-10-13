# Sprint 1 — UX + Foundation

**Dates:** Mon 6 – Thu 9 Oct 2026 (run ahead of the planned 19–30 Oct window)
**Goal:** Design the MVP 1 experience and stand up the project we will build it in.
**Closed:** Thu 9 Oct 2026 — see [Review & close-out](#review--close-out).

> The team finished ahead of the roadmap's placeholder dates, so Sprint 1 ran in the week reserved for Sprint 0's
> carry-over window. Both sets of carry-overs stayed open and are collected in [`../../homework/`](../../homework/README.md).

## Objectives

1. Agree the screens and flows for the three MVP 1 experiences: **school admin**, **driver**, **parent** (WhatsApp only).
2. Draft the WhatsApp message templates the parent promise depends on.
3. Stand up `backend/` + `frontend/` with Docker Compose and CI.
4. Close the technical questions that could still change the architecture (spikes).
5. Clear the client-dependent carry-over items from Sprint 0.

## Inputs

- Product brief: [`../product/product-brief.md`](../product/product-brief.md)
- MVP 1 scope: [`../product/mvp-scope.md`](../product/mvp-scope.md)
- Confirmed decisions: [`../DECISIONS.md`](../DECISIONS.md)
- Open client decisions: [`../product/owner-decisions.md`](../product/owner-decisions.md)
- Architecture decision + open technical questions: [`../architecture/architecture-decision.md`](../architecture/architecture-decision.md)
- UX: [`../ux/ux-research.md`](../ux/ux-research.md) · [`../ux/user-flows.md`](../ux/user-flows.md) · [`../ux/information-architecture.md`](../ux/information-architecture.md)
- Prototype screens, reference only: `src/routes/**` and [`../TAFI-CURRENT-STATE-AND-UX-DISCOVERY.md`](../TAFI-CURRENT-STATE-AND-UX-DISCOVERY.md)

## Tasks

> Owners are proposed by the team. **Confirm or swap them at the Sprint 1 kickoff (Mon 19 Oct).**

### UX and design — Anne (lead)

| ID | Task | Deliverable | Status |
|---|---|---|---|
| T1-01 | School admin flows: sign in, students + guardians, routes + stops, vehicles + drivers, assignments, notification log | Wireframes + updated `ux/information-architecture.md` | **Done** — four school portal screens in the deck; see [`../ux/wireframes.md`](../ux/wireframes.md) |
| T1-02 | Driver flows: today's trips, start/end trip, per child boarded / dropped off / absent, location-sharing state | Wireframes + updated `ux/user-flows.md` | **Done** — three crew app screens in the same deck |
| T1-03 | Parent experience: the four messages (trip started, boarded, bus approaching, dropped off) + absent, and what happens when a message fails | WhatsApp templates draft + template copy approved by the client | Not done — carried ([homework/sprint-1.md](../../homework/sprint-1.md)) |
| T1-04 | Retire the hypothesis labels that are now decided; keep `ASSUMPTION` only where it is still true | Updated product + UX docs | Not done — carried |
| T1-05 | Client review of MVP 1 scope and the `PROPOSED` rows in `owner-decisions.md` | Signed-off scope; decisions recorded in `DECISIONS.md` | Not done — carried |

### Foundation — Herman (lead)

| ID | Task | Deliverable | Status |
|---|---|---|---|
| T1-06 | Repo layout: `backend/` + `frontend/` in this repo; prototype preserved on a tag/archive branch | Committed scaffold + notes in `architecture-decision.md` | **Done** — `backend/` + `frontend/`; prototype at tag `prototype-lovable-2026-07` |
| T1-07 | Backend skeleton: FastAPI app, settings from env, structured logging, `/health`, Alembic, Pytest | Running API in Docker | **Done** — ruff, mypy and 7 tests pass |
| T1-08 | Frontend skeleton: React + Vite, routing, API client, design tokens, an accessible base layout | Running web app in Docker | **Done** — lint, typecheck and build pass on Node 22 |
| T1-09 | Local stack: Docker Compose for api + db + redis + worker; `.env.example`; no secrets in the repo | `docker compose up` works from a clean clone | **Done** — verified from a clean clone |
| T1-10 | CI: lint, typecheck and tests on every pull request | Green checks on a test PR | **Done** — both workflows green on the branch ([backend](https://github.com/annewaithaka/Tafi/actions/runs/37755490970), [frontend](https://github.com/annewaithaka/Tafi/actions/runs/37755491116)); they now run on every branch push as well as pull requests |

### Spikes — timeboxed, answers recorded in [`../architecture/architecture-decision.md`](../architecture/architecture-decision.md)

| ID | Question | Owner | Status |
|---|---|---|---|
| T1-11 | Can a phone browser keep sharing location while the screen is locked (Android and iPhone)? If not, what is the fallback? | Herman | **Done** — not reliable; wake lock trip mode |
| T1-12 | Maps and ETA: Google Maps vs an OpenStreetMap-based option; how "5 minutes away" is calculated and what it costs | Herman | **Done** — Leaflet + OSM, local ETA calculation |
| T1-13 | Worker: Celery vs RQ vs APScheduler plus a queue | Herman | **Done** — Celery kept |
| T1-14 | PostgreSQL: DigitalOcean Managed Database vs a container with a persistent volume | Herman | **Done** — managed in staging/production |
| T1-15 | WhatsApp Cloud API: template categories, approval time and the cost of a "utility" message | Anne | Not done — carried |

Answers are recorded in [`../architecture/spikes/sprint-1-spikes.md`](../architecture/spikes/sprint-1-spikes.md).

### Sprint 0 carry-over — must clear in the 7–16 Oct window

See [`sprint-0.md`](sprint-0.md#review--close-out) for C-01 to C-04.

## Deliverables

- Wireframes for the school admin, driver and parent experiences.
- Draft WhatsApp message templates ready to submit to Meta in Sprint 3.
- `backend/` + `frontend/` scaffold with Docker Compose and CI.
- Spike answers written into `architecture-decision.md`.
- Sprint 0 carry-over items cleared or re-dated with the client.

## Definition of Done

- [x] `docker compose up` starts api + db + redis + worker from a clean clone, and `/health` returns OK.
- [x] CI is green (lint, typecheck, backend tests) on the Sprint 1 branch.
- [ ] The client has reviewed and approved the wireframes and the MVP 1 scope (T1-05).
- [ ] WhatsApp templates are drafted and the client has confirmed the wording (T1-03).
- [ ] Every spike in T1-11 to T1-15 has a recorded answer (T1-11 to T1-14 are answered; T1-15 is not).
- [ ] Sprint 0 carry-over items C-01 to C-04 are closed, or re-dated with the client.

## Review & close-out

**Closed Thu 9 Oct 2026.** Two of the six Definition of Done items are met; the other four depend on the client and
move to [`homework/sprint-1.md`](../../homework/sprint-1.md). The client walkthrough originally booked for 30 Oct
now happens as the Sprint 2 demo.

### What Sprint 1 delivered

**Design (Anne).** An 11-screen high-fidelity wireframe deck covering the school portal, the crew app, the parent
messages and the operator view. It is a single self-contained HTML file served by the app at `/wireframes` and
openable straight from disk. Documented in [`../ux/wireframes.md`](../ux/wireframes.md).

**Foundation (Herman).** `backend/` (FastAPI, settings, logging, `/health`, Alembic, Celery worker, 7 tests),
`frontend/` (React + Vite + Tailwind on the prototype's design tokens, now split into a public side and a
protected side), a Docker Compose stack verified from a clean clone with an empty database, and GitHub Actions
CI green on both sides.

**Spikes.** T1-11 to T1-14 answered in [`../architecture/spikes/sprint-1-spikes.md`](../architecture/spikes/sprint-1-spikes.md).

### What was not finished

| Item | Left over | Owner | Where it goes |
|---|---|---|---|
| T1-03 | Approved WhatsApp template copy — the wireframes show the message designs, not final wording | Anne | [`homework/sprint-1.md`](../../homework/sprint-1.md) |
| T1-04 | Retiring the stale `ASSUMPTION` labels now that several are decided | Anne | homework |
| T1-05 | Client review and sign-off of the MVP 1 scope and the `PROPOSED` decisions | Anne | homework; blocks Sprint 3 |
| T1-15 | WhatsApp Cloud API spike (categories, approval time, cost) | Anne | homework; needed before Sprint 3 submits templates |
| C-01 to C-04 | Sprint 0 carry-overs, unchanged | Anne, Herman, client | [`sprint-0.md`](sprint-0.md#review--close-out) |
| Foundation PR | The branch is pushed and CI-green but the pull request is not open | Herman | homework |

### Notes for the close-out

- **The wireframes raise two scope questions.** The school portal navigation shows **Trips** and **Settings**,
  which MVP 1 does not list, and the parent section presents **Option A (WhatsApp + a registration page)** next to
  **Option B (a parent web dashboard)**. D-12 says parents use WhatsApp only, so Option B needs the client's
  answer (owner-decision row 9). Both are in the homework.
- **Nothing in the wireframes is built.** Screens 1–9 are targets for Sprints 3–5; screen 10 is not in MVP 1 and
  screen 11 is after it.
- Live trips, the message log and "needs attention" in screen 1 depend on the notification outbox, so they land
  with Sprint 5, not Sprint 3.

## Next sprint

**Sprint 2 (2–13 Nov): Auth + Tenancy.** Organizations, platform admin onboards a school and invites its first
admin, sign in, password reset, roles, and a staging deployment on DigitalOcean.

## Risks to watch

| Risk | Watch |
|---|---|
| Spikes eat the sprint | Timebox each to half a day; record the answer and move on |
| Wireframes reviewed too late to change the scope | Client review booked for the last week, not the last day |
| Term 3 ends before the user conversations happen | C-03 is a Sprint 0 item; do it in the 7–16 Oct window |
| Meta verification is slower than expected | C-04 started by the client now; templates drafted here so Sprint 3 can submit |
