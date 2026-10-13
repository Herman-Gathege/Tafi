# Sprint 3 — School Operations

> **Dates:** 14–28 Oct 2026 (target; was 16–27 Nov). **Owner:** Anne (D-25). **Reviewer:** Herman.
> **Branch:** `feature/sprint-3-school-operations`, from `feature/sprint-1-foundation` until the Sprint 1–2 pull
> request lands on `main`, then rebased onto `main`.

## Goal

A school can set up everything the parent messages depend on: its children, their guardians (with consent), its
routes and stops, its vehicles and its crew. Built to the approved wireframes (D-23): **Children & guardians**,
**Routes, vehicles & crew**, and the **registration page** a guardian reaches from the invite link.

## Decisions this sprint builds on

- **D-10** every new table carries `organization_id`; every route resolves the caller's membership first
  (pattern in `backend/app/api/deps.py`).
- **D-18** guardian invite links use the same hashed, single-use, expiring token, returned in the response in
  `local` only until Sprint 5.
- **D-21** driver required, conductor optional; `conductor` is a membership role.
- **D-22** registration both ways; the school owns child, route and stops; the guardian owns their contact details
  and consent; no messages before consent.
- **D-24** child cards table now, scanning later.

## Data model

All tables carry `organization_id`, `created_at` and `updated_at`. Rows that point at each other must belong to the
same organization; enforce it in the service layer and cover it with tests.

| Table | Key fields | Notes |
|---|---|---|
| `memberships` (existing) | `role` gains `conductor` | Migration adds the value; invite flow accepts it |
| `students` | first name, last name, class/grade, status (`active`, `inactive`) | Collect the minimum: no date of birth, no photo yet |
| `guardians` | full name, WhatsApp number (E.164, unique per organization), email (optional), status (`invited`, `confirmed`) | One guardian can be linked to several children |
| `student_guardians` | student, guardian, relationship, `is_primary`, `receives_messages` | At least one guardian per student |
| `guardian_consents` | guardian, consent text version, given at, method (`invite_link`, `school_recorded`), withdrawn at | Messaging is allowed only with a current, unwithdrawn consent |
| `guardian_invites` | guardian, token hash, expires at, used at | Same token pattern as D-18 |
| `emergency_contacts` | student, name, phone (E.164), relationship | Added by the school or the guardian |
| `stop_change_requests` | student, guardian, requested stop or free-text location, status (`pending`, `approved`, `declined`), decided by | The school decides |
| `routes` | code, name/area, active | |
| `stops` | route, name, landmark, sequence, latitude and longitude (nullable) | Sequence is the morning order; afternoon runs reverse it unless a run overrides |
| `vehicles` | plate, seats, active | Plate unique per organization |
| `route_runs` | route, direction (`morning`, `afternoon`), departure time, vehicle, driver membership (required), conductor membership (nullable) | A run is the unit the crew app and Sprint 4 trips start from |
| `student_route_assignments` | student, route, pickup stop, drop-off stop, active from, active to | One active assignment per student per direction |
| `child_cards` | student, code (random, unique, no personal data), status (`active`, `lost`, `revoked`), issued at, revoked at | Created now, unused until scanning (D-24) |

Sprint 4 adds `trips` and `boarding_events`; the events will store the marking membership and a `method`
(`manual`, later `scan`).

## Tasks

| ID | Task | Priority | Status |
|---|---|---|---|
| S3-01 | Migrations and models for the tables above, including the `conductor` role | P0 | Not started |
| S3-02 | Tenancy guard for every new route, with tests proving one school cannot read or change another's rows | P0 | Not started |
| S3-03 | Students API: list, search, create, edit, deactivate | P0 | Not started |
| S3-04 | Guardians API: create, link to students, set primary, E.164 validation, emergency contacts | P0 | Not started |
| S3-05 | Guardian invite: create and resend link; public registration page (wireframe "Registration page"): confirm details, add second guardian or emergency contact, give consent, request a stop change | P0 | Not started |
| S3-06 | Consent rules: record consent, withdraw consent, a single check `can_message(guardian)` for Sprint 5 to call | P0 | Not started |
| S3-07 | Routes and stops API: create routes, add and reorder stops | P0 | Not started |
| S3-08 | Vehicles, crew and route runs API: vehicles, invite driver or conductor, assign vehicle and crew to a run | P0 | Not started |
| S3-09 | Assign students to a route with pickup and drop-off stops | P0 | Not started |
| S3-10 | School portal screens: **Children & guardians** and **Routes, vehicles & crew**, matching the wireframes; stop-change requests list | P0 | Not started |
| S3-11 | CSV import of students and guardians, with a preview, per-row errors and no partial imports | P1 | Not started |
| S3-12 | WhatsApp template copy drafted (carries T1-03) and submitted to Meta once verification exists (C-04) | P0 | Blocked on client |
| S3-13 | Docs: `docs/architecture/data-model.md`; update `ux/wireframes.md` and `product/owner-decisions.md` for D-20 to D-24 | P1 | Not started |

## Suggested order

1. S3-01 and S3-02 together, so every later route is built on the guard.
2. Routes, stops, vehicles, crew (S3-07, S3-08): the smaller set, and the students need stops to be assigned to.
3. Students and guardians (S3-03, S3-04), then assignments (S3-09).
4. Invite, registration page and consent (S3-05, S3-06).
5. Screens (S3-10) as each API lands, then CSV import (S3-11).

## Definition of Done

- A school admin sets up a full roster — routes, stops, vehicles, crew, children, guardians and assignments — in
  under a day, from the portal or a CSV.
- A guardian opens an invite link, confirms their details and gives consent; `can_message` returns false before
  that and true after.
- A run cannot be saved without a driver; it saves with or without a conductor.
- Tenancy tests pass for every new route; a school admin from another school gets `403` or `404`.
- Ruff, mypy, frontend lint and all tests pass in CI.
- Screens match the approved wireframes and work at phone width.
- Pull request opened and reviewed by Herman.

## Out of scope

- The crew app and trips (Sprint 4).
- Sending any WhatsApp message or email, including the invite link outside `local` (Sprint 5).
- The parent web dashboard and parent sign-in (Sprint 5, D-20).
- Card scanning (later, D-24).
- Billing (Sprint 6).

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Meta Business verification not started | Templates cannot be submitted; Sprint 5 messaging slips | Raise with the client this week; copy is drafted regardless |
| Sprint 1–2 pull request still unmerged | Sprint 3 stacks on unreviewed work | Herman opens it (H2-2); rebase Sprint 3 onto `main` when it lands |
| Real phone numbers in test data | Children's personal data exposure | Seed and test data use made-up `+2547000000xx` numbers only |
| CSV formats vary by school | Import fails on real files | Publish a template file; validate and preview before saving |

## Review / close-out

_To be completed at the end of the sprint._
