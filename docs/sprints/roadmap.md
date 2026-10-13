# Tafi Roadmap

> Fits the 3–4 month window (D-11): 2-week sprints, pilot-ready by end of January 2027, pilot in Term 1.
> Dates are targets; adjust at each sprint review.

| Sprint | Dates | Status | Goal | Deliverables | Definition of Done |
|---|---|---|---|---|---|
| 0 — Discovery & Research | 5–16 Oct | ✅ Closed 6 Oct (C-01→C-04 carried) | Agree what Tafi is | Decisions, MVP 1 scope, user conversations, Sprint 1 plan | See [`sprint-0.md`](sprint-0.md) |
| 1 — UX + Foundation | 6–9 Oct (was 19–30 Oct) | ✅ Closed 9 Oct (T1-03, T1-04, T1-05, T1-15 carried) | Design the flows; stand up the base project | Wireframes (admin, driver, WhatsApp messages); `backend/` + `frontend/` scaffold; Docker Compose; CI; spike results | `docker compose up` runs api + db + redis + worker; CI green; see [`sprint-1.md`](sprint-1.md) |
| 2 — Auth + Tenancy | 2–13 Nov | Planned | Users, roles, organizations | Organizations, platform admin onboards a school, invites, sign in, password reset, roles; staging on DigitalOcean | A new school can be onboarded end to end on staging |
| 3 — School Operations | 16–27 Nov | Planned | Data the parent messages depend on | Students, guardians (multiple, consent), routes + stops, vehicles, drivers, assignments, CSV import; WhatsApp templates submitted to Meta | A school's full roster can be set up in under a day |
| 4 — Driver Trip App | 30 Nov–11 Dec | Planned | Record what happens on the bus | Driver web app: today's trips, start/end, boarded/dropped off/absent, location sharing | A test trip records every event and a location trail |
| 5 — Parent WhatsApp | 14–23 Dec | Planned | Deliver the promise | Outbox + worker; trip started, boarded, approaching, dropped off messages; notification log; live trip view | Guardians on a test trip receive every message, logged; no duplicates |
| — Holiday break | 24 Dec–3 Jan | — | — | — | — |
| 6 — Billing | 4–15 Jan | Planned | Money flows | School → parent fees (terms, invoices, payments); platform plans and pricing editable by client; Tafi → school invoices | Client changes a price without developers; balances correct |
| 7 — Hardening + Launch | 18–29 Jan | Planned | Pilot-ready | Critical-path tests, accessibility and security review, privacy checklist, production deploy, backups, monitoring, runbook | Production live; restore and rollback tested; pilot school onboarded |
| Pilot | From Feb 2027 | Planned | Validate with a real school | Weekly check-ins, fixes | Success metric agreed with client is measured |

## Notes

- **Sprint 0 closed 6 Oct 2026** with four carry-over items (C-01 to C-04) cleared in the 7–16 Oct window; see
  [`sprint-0.md`](sprint-0.md#review--close-out).
- **WhatsApp lead time:** Meta Business verification starts in Sprint 0; templates are submitted in Sprint 3 so
  they are approved before Sprint 5.
- **Staging from Sprint 2:** every sprint ends with a demo the client can click through.
- **Billing is the release valve:** if earlier sprints slip, Sprint 6 work moves after the pilot starts (pilot
  can run free).
- **School calendar:** user conversations must happen in October, before Term 3 closes.
