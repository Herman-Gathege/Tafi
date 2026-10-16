# Sprint 3 — School Operations

> **Dates:** 14 Oct 2026 (planned 14–28 Oct; was 16–27 Nov). **Owner:** Anne (D-25). **Reviewer:** Herman.
> **Status:** ✅ Closed 14 Oct 2026 (D-31) with S3-12 carried; see [Review / close-out](#review--close-out).
> **Branch:** `feature/sprint-3-school-operations`, from `feature/sprint-1-foundation` until the Sprint 1–2 pull
> request lands on `main`, then rebased onto `main`.

## Goal

A school can set up everything the parent messages depend on: its children, their guardians (with consent), its
routes and stops, its vehicles and its crew. Built to the approved wireframes (D-23): **Children & guardians**,
**Routes, vehicles & crew**, and the **registration page** a guardian reaches from the invite link.

## Decisions this sprint builds on

- **D-10** every new table carries `organization_id`; every route resolves the caller's membership first.
- **D-18** guardian invite links use the same hashed, single-use, expiring token, returned in the response in
  `local` only until Sprint 5.
- **D-21** driver required, conductor optional; `conductor` is a membership role.
- **D-22** registration both ways; the school owns child, route and stops; the guardian owns their contact details
  and consent; no messages before consent.
- **D-24** child cards table now, scanning later.

Decided during the sprint: **D-26** (which school a request acts in; other schools' rows are 404), **D-27**
(versioned consent wording, draft), **D-28** (route changes take effect today), **D-29** (guardians cannot change
their number from the link), **D-30** (all-or-nothing roster import).

## Data model

The tables as built are described in [`../architecture/data-model.md`](../architecture/data-model.md). Two
differences from the plan:

- `conductor` needed **no migration**: roles are stored as text, so it is a new value in the Python enum.
- A child has **one current route assignment** holding both the pickup and the drop-off stop, rather than one per
  direction (D-28).

## Tasks

| ID | Task | Priority | Status |
|---|---|---|---|
| S3-01 | Migrations and models, including the `conductor` role | P0 | ✅ Done — migration `0003_school_operations`, 13 tables |
| S3-02 | Tenancy guard for every new route, with tests proving one school cannot read or change another's rows | P0 | ✅ Done — `SchoolAdmin`, `Crew`, `get_owned_or_404` (D-26) |
| S3-03 | Students API: list, search, create, edit, deactivate | P0 | ✅ Done |
| S3-04 | Guardians API: create, link to students, set primary, E.164 validation, emergency contacts | P0 | ✅ Done |
| S3-05 | Guardian invite link and public registration page | P0 | ✅ Done |
| S3-06 | Consent rules: record, withdraw, `can_message(guardian)` for Sprint 5 | P0 | ✅ Done — `backend/app/services/consent.py` (D-27) |
| S3-07 | Routes and stops API: create routes, add and reorder stops | P0 | ✅ Done |
| S3-08 | Vehicles, crew and route runs API | P0 | ✅ Done |
| S3-09 | Assign students to a route with pickup and drop-off stops | P0 | ✅ Done (D-28) |
| S3-10 | School portal screens: Children & guardians, Routes & crew, stop-change requests; guardian registration page | P0 | ✅ Done |
| S3-11 | CSV import with a preview, per-row errors and no partial imports | P1 | ✅ Done (D-30) |
| S3-12 | WhatsApp template copy drafted and submitted to Meta | P0 | ⛔ Carried — blocked on the client's Meta verification (C-04) |
| S3-13 | Docs: data model, wireframes, owner decisions, close-out | P1 | ✅ Done |

## Definition of Done

| Item | Met? |
|---|---|
| A school admin sets up a full roster in under a day, from the portal or a CSV | ✅ Walked through end to end on the running stack, by hand and by importing the spreadsheet template |
| A guardian opens an invite link, confirms and consents; `can_message` is false before and true after | ✅ Tested (`tests/test_guardian_invites.py`) and walked through in a browser |
| A run cannot be saved without a driver; it saves with or without a conductor | ✅ Enforced by the database and the API, and tested |
| Tenancy tests pass for every new route; another school's admin gets `403` or `404` | ✅ Every new route file has a cross-school test |
| Ruff, mypy, frontend lint and all tests pass | ✅ 114 backend tests; ruff, mypy, ESLint and TypeScript clean |
| Screens match the approved wireframes and work at phone width | 🟡 Built to the wireframes and checked in a desktop browser; **not yet checked on a real phone** (carried) |
| Pull request opened and reviewed by Herman | ❌ Carried — it stacks on the unmerged Sprint 1–2 branch (H2-2) |

## Out of scope

- The crew app and trips (Sprint 4).
- Sending any WhatsApp message or email, including the invite link outside `local` (Sprint 5).
- The parent web dashboard and parent sign-in (Sprint 5, D-20).
- Card scanning (later, D-24).
- Billing (Sprint 6).

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Meta Business verification not started | Templates cannot be submitted; Sprint 5 messaging slips | Raise with the client now; template copy can be drafted regardless |
| Sprint 1–3 work unmerged and unreviewed | Three sprints stack on one branch | Herman opens the pull requests (H2-2, H3-3) |
| Consent wording is a draft | Guardians would agree to text the client has not approved | Client approves it and names a privacy contact before the pilot (H3-1) |
| Real phone numbers in test data | Children's personal data exposure | Tests and the CSV template use made-up `+2547000000xx` numbers only |

## Review / close-out

**Closed 14 Oct 2026 (D-31).** Every task the team could do alone is done.

**What was built**

- **Backend:** 13 tables (`0003_school_operations`); access checks for school admins and crew; endpoints for
  students, guardians, emergency contacts, routes, stops, runs, vehicles, crew, route assignments with history,
  guardian invites, consent, stop-change requests and roster import. 90 new tests (114 in total).
- **Frontend:** Children & guardians (`/app/children`) with the child panel and spreadsheet import; Routes & crew
  (`/app/routes`); Stop requests (`/app/requests`); the public guardian registration page (`/guardian-invite`).
- **Ready for Sprint 5:** `can_message(guardian)` in `backend/app/services/consent.py`.

**Carried** (details in [`../../homework/sprint-3.md`](../../homework/sprint-3.md))

- S3-12, WhatsApp templates: blocked on the client's Meta Business verification.
- Herman's review of the Sprint 3 work, once the Sprint 1–2 pull request is open.
- A check of the four new screens on a real phone.
- The consent wording and privacy contact: client approval.

**Learned**

- Building API, tests and screens per task in one pass kept each step reviewable and green.
- Verifying the frontend types against the API's OpenAPI schema caught mismatches before they reached a browser;
  keep doing it in Sprint 4.
- Local ports clash with other projects on the same machine; `.env` must set `VITE_API_BASE_URL`, `CORS_ORIGINS`
  and `APP_PUBLIC_URL` together when the ports move (see the walkthrough).

**Next:** Sprint 4, the crew trip app, can start early. Pull its dates forward at planning.
