# Tafi Decision Log

> Only **confirmed** decisions go here. Open items live in
> [`product/owner-decisions.md`](product/owner-decisions.md).
> Approved by: **Client** (product owner) or **Team** (Anne + Herman, for delivery/technical decisions).

| ID | Date | Decision | Reason | Alternatives considered | Approved by |
|---|---|---|---|---|---|
| D-01 | 2026-10-04 | Discovery/planning work happens on branch `codex/tafi-discovery-foundation`; `main` stays clean | Reviewable changes; `main` stays stable | Work on `main` (rejected) | Team |
| D-02 | 2026-10-04 | Sprint 0 is documentation/research only — **except security hygiene** (repo visibility, untracking secrets), allowed from 2026-10-05 | Establish direction before building; secrets exposure can't wait | Start implementation now (rejected) | Team |
| D-03 | 2026-10-05 | The client is the product owner and approves product decisions; Anne and Herman are the developers | Clarifies who signs off | — | Team |
| D-04 | 2026-10-05 | Tafi is a **parent safety service**: parents receive WhatsApp updates such as "boarded bus KCA 123X at 6:42" and "bus is 5 minutes away" | Client's product idea; matches the landing page | School-ops-only tool (rejected as the end goal) | Client |
| D-05 | 2026-10-05 | **MVP 1 serves schools**; the product broadens to other transport providers later | Schools are the first buyers; narrow scope fits the timeline | All transport providers in MVP 1 (deferred) | Client |
| D-06 | 2026-10-05 | Billing model: **Tafi bills schools; schools bill parents** for transport fees | Client confirmation | Parents pay Tafi directly (not chosen) | Client |
| D-07 | 2026-10-05 | Platform pricing is **configurable by the client in the app** without developer involvement; KES 450/child/month is a placeholder | Pricing will change with market factors | Hard-coded pricing (rejected) | Client |
| D-08 | 2026-10-05 | **Rebuild** on the team stack: React · FastAPI · PostgreSQL · SQLAlchemy/Alembic · Redis · worker · Docker Compose · DigitalOcean | Team's production stack; native home for WhatsApp/background jobs; full data control | Keep the Supabase/TanStack prototype (rejected) | Team (client acknowledgement pending) |
| D-09 | 2026-10-05 | **Lovable is not used.** The prototype is reference material for screens, flows and data model only | Rebuild per D-08 | Continue in Lovable (rejected) | Team |
| D-10 | 2026-10-05 | Tenancy is a generic **organization** with a type (`school` now, operators later) | Keeps D-05's later broadening cheap | School as hard-coded tenant root (rejected) | Team |
| D-11 | 2026-10-05 | Delivery window: **3 months, 4 max**; pilot-ready by end of January 2027 | Team capacity and client expectation | — | Team |
| D-12 | 2026-10-05 | Parents use **WhatsApp only** in MVP 1 — no parent app | Client: "parents on WhatsApp"; matches market pattern | Parent app (rejected for MVP 1) | Client |
| D-13 | 2026-10-06 | **Sprint 0 is closed** with four carry-over items (C-01 to C-04) owned and dated in [`sprints/sprint-0.md`](sprints/sprint-0.md#review--close-out). No MVP code was written in Sprint 0 | The remaining exit criteria are client- or interview-dependent; holding the sprint open does not unblock them | Keep Sprint 0 open until 16 Oct (rejected: no benefit, delays Sprint 1 prep) | Team |

<!-- Add new confirmed decisions with the next ID. -->
