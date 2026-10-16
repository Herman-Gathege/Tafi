# Tafi Roadmap

> Fits the 3–4 month window (D-11): 2-week sprints, pilot-ready by end of January 2027, pilot in Term 1.
> Dates are targets; adjust at each sprint review. Sprints 1–3 finished early.

| Sprint | Dates | Status | Goal | Deliverables | Definition of Done |
|---|---|---|---|---|---|
| 0 — Discovery & Research | 5–16 Oct | ✅ Closed 6 Oct (C-01→C-04 carried) | Agree what Tafi is | Decisions, MVP 1 scope, user conversations, Sprint 1 plan | See [`sprint-0.md`](sprint-0.md) |
| 1 — UX + Foundation | 6–9 Oct (was 19–30 Oct) | ✅ Closed 9 Oct (T1-03, T1-04, T1-05, T1-15 carried) | Design the flows; stand up the base project | Wireframes; `backend/` + `frontend/` scaffold; Docker Compose; CI; spike results | See [`sprint-1.md`](sprint-1.md) |
| 2 — Auth + Tenancy | 13 Oct (was 2–13 Nov) | ✅ Closed 13 Oct (S2-07 carried) | Users, roles, organizations | Organizations, onboarding, invites, sign in, password reset, roles; staging configuration | Onboarding verified against the running stack |
| 3 — School Operations | 14 Oct (was 16–27 Nov) | ✅ Closed 14 Oct (S3-12 carried) · owner Anne (D-25) | Data the parent messages depend on | Conductor role; children, guardians, emergency contacts; guardian link with consent; routes, stops, vehicles, crew, runs; route assignments; roster import; school portal screens | A school's full roster can be set up in under a day — met; see [`sprint-3.md`](sprint-3.md) |
| 4 — Crew Trip App | 16 Oct (was 30 Nov–11 Dec) | Built and verified 16 Oct; real-phone check and review outstanding · [plan](sprint-4.md) | Record what happens on the bus | Crew web app for driver or conductor: today's trips, start/end, boarded/dropped off/absent, location sharing; driver-alone marks only when stopped; boarding events record who and how | A test trip records every event and a location trail — met on the running stack |
| 5 — Parent WhatsApp + Dashboard | 14–23 Dec | Planned | Deliver the promise | Outbox + worker; trip started, boarded, approaching, dropped off messages (checked against `can_message`); notification log; live trip view; invite and reset links delivered for real (D-18); parent web dashboard with one-time-code sign-in (D-20) | Guardians on a test trip receive every message, logged, no duplicates; a parent signs in and sees the trip |
| — Holiday break | 24 Dec–3 Jan | — | — | — | — |
| 6 — Billing | 4–15 Jan | Planned | Money flows | School → parent fees; platform plans and pricing editable by client; Tafi → school invoices | Client changes a price without developers; balances correct |
| 7 — Hardening + Launch | 18–29 Jan | Planned | Pilot-ready | Critical-path tests, accessibility and security review (refresh tokens, CSRF, rate limiting: D-17), privacy checklist, production deploy, backups, monitoring, runbook | Production live; restore and rollback tested; pilot school onboarded |
| Pilot | From Feb 2027 | Planned | Validate with a real school | Weekly check-ins, fixes | Success metric agreed with client is measured |

## Notes

- **Sprints 1–3 finished in October.** Pull Sprint 4 forward at its planning rather than leaving a gap; the extra
  time is the best buffer for Sprint 5 (WhatsApp and the parent dashboard) and for Meta's approval times.
- **WhatsApp lead time is now the main schedule risk.** Meta Business verification is still owed by the client
  (C-04); templates (S3-12) cannot be submitted without it, and approved templates are needed before Sprint 5.
- **The parent dashboard (D-20) adds work to Sprint 5.** WhatsApp messages come first; if the sprint runs long, the
  dashboard moves into January ahead of billing.
- **Billing is the release valve:** if earlier sprints slip, Sprint 6 work moves after the pilot starts (pilot
  can run free).
- **Child card scanning (D-24)** is after the pilot; Sprints 3 and 4 prepare the data for it.
- **Staging:** every sprint should end with a demo the client can click through, once the client provides a
  DigitalOcean account.
- **School calendar:** user conversations must happen before Term 3 closes.
