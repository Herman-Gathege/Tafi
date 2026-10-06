# Sprint 1 — UX + Foundation

**Dates:** Mon 19 Oct – Fri 30 Oct 2026 (2 weeks)
**Goal:** Design the MVP 1 experience and stand up the project we will build it in.

> Sprint 0 closed on 6 Oct with four carry-over items ([`sprint-0.md`](sprint-0.md#review--close-out)).
> The 7–16 Oct window is used to clear those items; Sprint 1 starts on Mon 19 Oct as planned.

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
| T1-01 | School admin flows: sign in, students + guardians, routes + stops, vehicles + drivers, assignments, notification log | Wireframes + updated `ux/information-architecture.md` | Not started |
| T1-02 | Driver flows: today's trips, start/end trip, per child boarded / dropped off / absent, location-sharing state | Wireframes + updated `ux/user-flows.md` | Not started |
| T1-03 | Parent experience: the four messages (trip started, boarded, bus approaching, dropped off) + absent, and what happens when a message fails | WhatsApp templates draft + template copy approved by the client | Not started |
| T1-04 | Retire the hypothesis labels that are now decided; keep `ASSUMPTION` only where it is still true | Updated product + UX docs | Not started |
| T1-05 | Client review of MVP 1 scope and the `PROPOSED` rows in `owner-decisions.md` | Signed-off scope; decisions recorded in `DECISIONS.md` | Not started |

### Foundation — Herman (lead)

| ID | Task | Deliverable | Status |
|---|---|---|---|
| T1-06 | Repo layout: `backend/` + `frontend/` in this repo; prototype preserved on a tag/archive branch | Committed scaffold + notes in `architecture-decision.md` | Not started |
| T1-07 | Backend skeleton: FastAPI app, settings from env, structured logging, `/health`, Alembic, Pytest | Running API in Docker | Not started |
| T1-08 | Frontend skeleton: React + Vite, routing, API client, design tokens, an accessible base layout | Running web app in Docker | Not started |
| T1-09 | Local stack: Docker Compose for api + db + redis + worker; `.env.example`; no secrets in the repo | `docker compose up` works from a clean clone | Not started |
| T1-10 | CI: lint, typecheck and tests on every pull request | Green checks on a test PR | Not started |

### Spikes — timeboxed, answers recorded in [`../architecture/architecture-decision.md`](../architecture/architecture-decision.md)

| ID | Question | Owner | Status |
|---|---|---|---|
| T1-11 | Can a phone browser keep sharing location while the screen is locked (Android and iPhone)? If not, what is the fallback? | Herman | Not started |
| T1-12 | Maps and ETA: Google Maps vs an OpenStreetMap-based option; how "5 minutes away" is calculated and what it costs | Herman | Not started |
| T1-13 | Worker: Celery vs RQ vs APScheduler plus a queue | Herman | Not started |
| T1-14 | PostgreSQL: DigitalOcean Managed Database vs a container with a persistent volume | Herman | Not started |
| T1-15 | WhatsApp Cloud API: template categories, approval time and the cost of a "utility" message | Anne | Not started |

### Sprint 0 carry-over — must clear in the 7–16 Oct window

See [`sprint-0.md`](sprint-0.md#review--close-out) for C-01 to C-04.

## Deliverables

- Wireframes for the school admin, driver and parent experiences.
- Draft WhatsApp message templates ready to submit to Meta in Sprint 3.
- `backend/` + `frontend/` scaffold with Docker Compose and CI.
- Spike answers written into `architecture-decision.md`.
- Sprint 0 carry-over items cleared or re-dated with the client.

## Definition of Done

- [ ] `docker compose up` starts api + db + redis + worker from a clean clone, and `/health` returns OK.
- [ ] CI is green (lint, typecheck, backend tests) on the Sprint 1 pull requests.
- [ ] The client has reviewed and approved the wireframes and the MVP 1 scope (T1-05).
- [ ] WhatsApp templates are drafted and the client has confirmed the wording (T1-03).
- [ ] Every spike in T1-11 to T1-15 has a recorded answer, or an explicit "decide in Sprint 2".
- [ ] Sprint 0 carry-over items C-01 to C-04 are closed, or re-dated with the client.

## Review

**Fri 30 Oct, 30 minutes — Anne, Herman and the client.** Walk through the wireframes, the project scaffold and
the spike results. Confirm the Sprint 2 goal (auth + tenancy) and any scope change.

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
