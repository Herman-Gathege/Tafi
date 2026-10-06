# Tafi Status

_Last updated: 6 Oct 2026_

**Phase:** Sprint 1 — UX + Foundation (19–30 Oct 2026). **Sprint 0 closed 6 Oct 2026.**

**Current objective:** Design the MVP 1 flows and stand up the project scaffold, and clear the four Sprint 0
carry-over items in the 7–16 Oct window.

## Decided (see [`DECISIONS.md`](DECISIONS.md))

- The client is the product owner; Anne and Herman are the developers.
- Tafi is a **parent safety service**: parents get WhatsApp updates about their child's trip.
- **MVP 1 serves schools.** Other transport providers come later; the data model must allow for them.
- Billing: **Tafi bills schools; schools bill parents** for transport.
- Platform pricing is **configurable by the client** without developers. KES 450/child/month is a placeholder.
- **Rebuild on the team stack** (FastAPI · React · PostgreSQL · Redis · Docker · DigitalOcean). Lovable is not used.
- Delivery window: **3 months, 4 max** → pilot-ready by end of January 2027.

## In progress

- Sprint 1 UX and foundation work ([`sprints/sprint-1.md`](sprints/sprint-1.md)).
- Four Sprint 0 carry-over items C-01 to C-04 ([`sprints/sprint-0.md`](sprints/sprint-0.md#review--close-out)).

## Waiting on the client

- Whether the prototype backend holds any real data; switch the prototype backend off once confirmed.
- Meta Business verification and a dedicated phone number for Tafi's WhatsApp.
- Introduction to at least one candidate pilot school.
- Acknowledgement of the rebuild plan and timeline.
- Review of the MVP 1 scope and the `PROPOSED` rows in [`product/owner-decisions.md`](product/owner-decisions.md).

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| **Both GitHub repos are public and `.env` is still in git history** | Exposed Supabase keys and a Google Maps browser key | C-02: make repos private, rotate the keys, purge history — **most urgent open item** |
| WhatsApp Business verification and template approval take time | Parent messages blocked in Sprint 5 | Client starts verification in Sprint 0; templates submitted by Sprint 3 |
| School calendar: Term 3 usually closes late Oct/early Nov; schools reopen in January | No one to interview or pilot with over the holidays | User conversations in October; pilot in Term 1 2027 |
| "Bus approaching" needs live location from a driver's phone; browsers may pause location when the screen locks (especially iPhone) | Core parent message unreliable | Sprint 1 technical spike before committing to an approach |
| No pilot school yet | Nothing to validate against | Client introduction is a Sprint 0 action |
| Children's personal data (Kenya Data Protection Act 2019) | Legal and trust risk | Privacy check in Sprint 1; guardian consent built into MVP 1 |
| 3–4 month window is tight | Scope creep delays pilot | 2-week sprints, strict MVP scope, billing can move after pilot if needed |

## Next

Clear C-01 to C-04 (by 16 Oct) → Sprint 1 kickoff Mon 19 Oct → Sprint 1 review + client demo Fri 30 Oct →
Sprint 2 (auth + tenancy) from Mon 2 Nov.
