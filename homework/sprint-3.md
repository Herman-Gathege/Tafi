# Homework — Sprint 3

> Sprint 3 closed Tue 14 Oct 2026 with every task done except S3-12. Source:
> [`../docs/sprints/sprint-3.md`](../docs/sprints/sprint-3.md#review--close-out).

## Client

### H3-1 — Approve the consent wording and name a privacy contact

- **Left over:** guardians agree to a **draft** text (`2026-10-draft`) that ends with "[privacy contact to be
  confirmed]".
- **Why it matters:** no guardian of the pilot school should consent to wording the client has not approved; the
  Kenya Data Protection Act 2019 expects a contact for data questions.
- **Next action:** Anne sends the text to the client; the client approves or edits it (ideally with their lawyer)
  and names the contact. The team changes `CONSENT_TEXT` and bumps `CONSENT_VERSION` in
  `backend/app/services/consent.py`.
- **Tracked:** D-27, MVP-22, owner decisions 21 and 22.

### H3-2 — Meta Business verification and a WhatsApp number (blocks S3-12)

- **Left over:** verification has not started, so the WhatsApp message templates cannot be submitted.
- **Why it matters:** approval can take weeks, and Sprint 5 needs approved templates. This is now the main risk to
  the schedule.
- **Next action:** Anne asks the client to start this week, together with the staging account (H2-5).
- **Tracked:** S3-12, C-04, owner decision 17.

## Herman

### H3-3 — Review Sprint 3

- **Left over:** the Sprint 3 work is pushed on `feature/sprint-3-school-operations` but unreviewed. It stacks on
  the Sprint 1–2 branch, which has no pull request yet (H2-2).
- **Why it matters:** three sprints of unreviewed work; the Definition of Done asks for Herman's review.
- **Next action:** after the Sprint 1–2 pull request is open, open one for Sprint 3 and review it, starting with
  `backend/app/api/deps.py` (D-26) and the migration `0003_school_operations`.
- **Tracked:** D-25, D-31.

## Anne

### H3-4 — Check the new screens on a real phone

- **Left over:** Children & guardians, Routes & crew, Stop requests and the guardian page were checked in a desktop
  browser only. The guardian page in particular will mostly be opened on phones.
- **Next action:** open them on an Android phone on the same network (`http://<laptop-ip>:<WEB_PORT>`), fix
  anything that overflows or is too small to tap, and note it here.
- **Tracked:** MVP-19.

## Notes for the next sprint

- **Sprint 4 can start now.** Its trips start from `route_runs` (driver required, conductor optional) and the
  children's current `student_route_assignments`; boarding events must record the marking membership and a
  `method` (D-21, D-24). The crew routes use the `Crew` dependency in `backend/app/api/deps.py`.
- A crew member who already has a Tafi account cannot accept an invite to a second school (MVP-27). Not a problem
  for a one-school pilot.
- Keep checking the frontend types against the API (the OpenAPI comparison caught mismatches in Sprint 3).
