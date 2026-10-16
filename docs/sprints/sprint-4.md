# Sprint 4 — Crew Trip App

> **Dates:** 30 Nov – 11 Dec 2026 on the roadmap, and marked "can start early"; the start date is a decision for the
> project lead at planning. **Status:** planned, not started. Written 16 Oct 2026.
> **Branch:** to be cut from `feature/sprint-3-school-operations` until the Sprint 1–3 pull requests land on `main`.

## Goal

**Record what happens on the bus** — a trip the crew can start and end, and a boarding record of who got on, who got
off and who was absent, with a location trail while the trip is running.

## Decisions this sprint builds on

- **D-21** every route run has a **driver (required)** and a **conductor (optional)**; whoever is crew marks children
  on and off; when the driver is alone the app only allows marking while the vehicle is stopped; every event records
  who marked it and how.
- **D-24** child cards come later. The data prepares for them now: a boarding event carries a `method`
  (`manual` now, `scan` later).
- **D-26** every route resolves the caller's school first; another school's row is reported as **404**.
- **D-28** a child has at most one current route assignment, holding both the pickup and the drop-off stop.
- **D-18** nothing sends WhatsApp or email yet, so a trip records events for Sprint 5 to deliver; the crew app must
  not imply a parent has been messaged.

## What already exists (verified against the code on 16 Oct 2026)

| Already there | Where |
|---|---|
| `route_runs`: one per route per direction, **driver not null**, conductor optional, unique on `(route_id, direction)` | `backend/app/models/transport.py`, migration `0003_school_operations` |
| `student_route_assignments`: one active assignment per child (partial unique index), with history | same |
| `Crew` dependency — a `driver` or `conductor` membership, tenant-resolved | `backend/app/api/deps.py:105` (`CREW_ROLES` in `backend/app/models/user.py:29`) |
| Stops with a sequence, vehicles, routes, crew invitations and the crew list | `backend/app/api/routes/school_transport.py`, `school_crew.py` |
| Children, guardians, emergency contacts, consent | `backend/app/api/routes/school_students.py`, `school_guardians.py` |
| `can_message(guardian)` and `consented_guardian_ids(...)`, ready for Sprint 5 | `backend/app/services/consent.py` |
| 114 backend tests, ruff, mypy, ESLint, TypeScript and the production build all pass | verified 16 Oct 2026 |

**Missing, and confirmed absent by search:** there is no `trips` table or model, no `boarding_events`, no trip or
boarding endpoint, no crew screen and no location handling anywhere in the repository. Sprint 4 builds all of it.

## Data model (planned — not implemented)

The shape describes what Sprint 4 is expected to add, following
[`../architecture/data-model.md`](../architecture/data-model.md). Every table carries `organization_id` (D-10) and is
read through `get_owned_or_404` (D-26).

```text
trips(id, organization_id, route_run_id, service_date, status, started_at, ended_at,
      started_by_membership_id, ended_by_membership_id, created_at, updated_at)
      # unique on (route_run_id, service_date) — one trip per run per day
      # status: scheduled → active → completed (and cancelled)

boarding_events(id, organization_id, trip_id, student_id, kind, recorded_by_membership_id,
                method, recorded_at, latitude, longitude, created_at)
      # kind: boarded | dropped_off | absent
      # method: manual (scan arrives with D-24)
      # recorded_by_membership_id is the attribution D-21 requires

trip_locations(id, organization_id, trip_id, recorded_at, latitude, longitude,
               accuracy_m, recorded_by_membership_id)
      # proposed here to satisfy MVP-11 ("location is shared during an active trip");
      # the data-model page lists trips and boarding events but not a location store
```

## Tasks

| ID | Task | Priority |
|---|---|---|
| S4-01 | Models and migration `0004_crew_trips`: `trips`, `boarding_events`, `trip_locations` | P0 |
| S4-02 | Trip lifecycle API: start and end a trip, with valid state transitions only | P0 |
| S4-03 | Boarding API: mark a child boarded, dropped off or absent, recording the crew membership and the method | P0 |
| S4-04 | Domain rules: no second boarding without a drop-off, no events on a finished trip, no events for a child not assigned to the run — with clear errors | P0 |
| S4-05 | The driver-alone stopped rule, enforced **by the API** using the mechanism chosen in decision A | P0 |
| S4-06 | Location ingest for an active trip, and the crew UI for permission, signal loss and battery | P0 (see decision C) |
| S4-07 | Crew web screens built to wireframes 5, 6 and 7: today's trips, mark children, trip complete | P0 |
| S4-08 | Tests: lifecycle transitions, event ordering, duplicate and invalid events, permissions, tenant isolation, location association — deterministic, with a controlled clock | P0 |
| S4-09 | Documentation: data model, wireframe mapping, STATUS, backlog, and a Sprint 4 delivery page | P1 |
| S4-10 | Real-phone check of the crew flow | P1 |

## Definition of Done

- [ ] A test trip records every event and a location trail (the roadmap's own wording).
- [ ] Authorised crew can reach **only** their permitted trips, enforced by the API rather than by hiding buttons.
- [ ] Trips start and end only through valid state transitions; an invalid transition is refused.
- [ ] Boarded, dropped-off and absent events persist, each with the responsible crew membership and the recording
      method.
- [ ] Invalid or duplicate events are handled consistently with the rules above.
- [ ] The driver-alone restriction is enforced by the backend using the approved mechanism from decision A.
- [ ] Location updates are tied to the correct active trip and stored per the data model.
- [ ] Location permission, signal loss and battery failures each have an explicit user experience.
- [ ] The crew flow is usable on a real phone.
- [ ] Automated tests cover the business rules and the important failure paths, without timing-dependent flakiness.
- [ ] Sprint 3's suite still passes (regression).
- [ ] The migration path is valid and reversible.
- [ ] Documentation and acceptance criteria match the implementation.

## Open decisions (project lead)

### A. How does a driver working alone prove the vehicle is stopped?

A browser gives no reliable speed or motion signal — geolocation reports position, not velocity, and it stalls
entirely when the screen locks (T1-11). Options:

1. **Hold-to-confirm** — the crew member presses and holds an "I am stopped" control before the mark buttons unlock.
   Enforced server-side by requiring a recent confirmation timestamp with each event. *Recommended:* testable today,
   no hardware, and it puts the acknowledgement on the person who knows.
2. **Minimum time between marks** — refuse two events within, say, 20 seconds. Cheap, but it only limits speed, it
   does not establish that the vehicle stopped.
3. **Defer to a native app** later, where motion data is available. Safest technically, but Sprint 4 is a web app.

### B. Location sharing

The Sprint 1 spike ([`../architecture/spikes/sprint-1-spikes.md`](../architecture/spikes/sprint-1-spikes.md), T1-11)
established that a phone browser **cannot** keep sending location while the screen is locked. The plan is therefore a
wake-lock "trip mode" with a keep-this-screen-open state — and **wake lock is not a guarantee**: iOS Safari under
18.4 does not honour it in a Home Screen web app, the lock is released whenever the tab is hidden, and a dead battery
ends it regardless. Required behaviour:

- Boarded, dropped-off and absent are **taps** and always work, with or without location.
- If location stops mid-trip, the trip keeps recording events, the gap is logged, and "bus approaching" is marked
  unavailable for that trip rather than guessed.
- Permission denied, a lost signal and a flat battery each get a plain explanation on screen, not a silent failure.

### C. Does location ship inside Sprint 4, or split out?

Location is MVP-11 and the roadmap lists it in Sprint 4, but it is the least certain piece and the only one that can
be blocked by a device. Options: keep it in (one sprint, one demo, higher risk), or ship the trip and boarding flow
first and take location as the first task of Sprint 5, where it already feeds the "bus approaching" message. **This
is the project lead's call**, and it changes S4-06 and the Definition of Done.

## Out of scope

- Parent WhatsApp messages, the notification log and the parent dashboard (Sprint 5, D-20).
- The school admin live trip view (MVP-15, Sprint 5).
- Billing and pricing (Sprint 6).
- Card scanning and NFC/QR decisions (later, D-24).
- Anything that sends a message: nothing is delivered until Sprint 5 (D-18).

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Location cannot be relied on in a browser | The "bus approaching" promise weakens | Decisions B and C; events never depend on location |
| The crew app is phone-only and has only been checked on a desktop so far | The people who use it most are least tested | S4-10 on a real phone, plus the outstanding Sprint 3 phone check |
| Three sprints are unmerged and unreviewed | Problems surface late; the branch keeps growing | Open the pull requests before Sprint 4 starts |
| Meta verification has not started (client) | Sprint 5 messaging slips | Raise it now; it does not block Sprint 4 |
| Nothing is deployed (client) | No demo the client can click | Staging config is ready; needs a DigitalOcean account |

## Review

To be held at the end of the sprint, with the client demo owed from Sprint 3 rolled into it. Confirm the Sprint 5 goal
(parent WhatsApp and the dashboard) and any scope change.

## Next sprint

**Sprint 5 — Parent WhatsApp + Dashboard** (14–23 Dec, D-20): the outbox and worker, the four parent messages checked
against `can_message`, the notification log, live trip view, real invite and reset delivery (D-18), and the parent web
dashboard with one-time-code sign-in.
