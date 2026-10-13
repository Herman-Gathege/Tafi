# Sprint 0 — Project Discovery & Research

**Dates:** Mon 5 Oct – Fri 16 Oct 2026
**Goal:** Understand what Tafi should become before we decide what to build.
**Closed:** Mon 6 Oct 2026 (team close-out; four carry-over items, see below).

## Tasks

### Discovery and research

- [x] Review the prototype (discovery report)
- [x] Research competitors
- [x] UX research framework, user flows, IA draft
- [x] Technical research plan and architecture options

### Decisions

- [x] Confirm who the product owner is (client — D-03)
- [x] Confirm product direction (parent safety service — D-04)
- [x] Confirm first customer (schools — D-05)
- [x] Confirm billing model (D-06) and configurable pricing (D-07)
- [x] Decide architecture (rebuild — D-08) and drop Lovable (D-09)
- [x] Agree delivery window (D-11)
- [ ] Client acknowledges the rebuild plan and timeline — Anne — **carried as C-01**
- [ ] Review MVP 1 scope and `PROPOSED` decisions with the client — Anne — **carried as C-01**

### Security hygiene (allowed by D-02)

- [ ] Make the GitHub repo private (`annewaithaka/Tafi` is the only repo — D-15) — **still open, carried as C-02**
- [x] Stop tracking `.env` and ignore env files (`fix/untrack-env`, reviewed by Herman) — Anne
- [x] Ask the client whether the prototype backend holds real data — Anne — **done 6 Oct:** test data only,
      nothing paid for besides Lovable; client approved deleting the Lovable project (D-14)
- [ ] Client disconnects GitHub from the Lovable project, then deletes it — **carried as C-04**

### Client actions (long lead time — start now)

- [ ] Client starts Meta Business verification and gets a dedicated phone number for Tafi's WhatsApp — **carried as C-04**
- [ ] Client introduces at least one candidate pilot school — **carried as C-04**

### User research

- [ ] At least 2 conversations (school transport admin, driver, parent) before schools close for the term —
      Anne — **carried as C-03**
- [ ] Record findings in `docs/ux/ux-research.md` — **carried as C-03**

### Close-out

- [ ] Update product docs with research findings — **carried as C-03**
- [x] Write [`sprint-1.md`](sprint-1.md)
- [x] Sprint 0 review — team, Mon 6 Oct 2026

## Deliverables

- Updated: `AGENTS.md`, `README.md`, `docs/README.md`, `docs/STATUS.md`, `docs/DECISIONS.md`
- Updated: `docs/product/{owner-decisions,product-brief,mvp-scope}.md`
- Updated: `docs/architecture/architecture-decision.md`
- Updated: `docs/sprints/{roadmap,backlog,sprint-0}.md`
- New: `docs/sprints/sprint-1.md`
- User conversation notes in `docs/ux/ux-research.md`

## Definition of Done (exit criteria)

- [x] Product direction, first customer and billing model recorded in `DECISIONS.md`
- [x] Architecture direction decided
- [ ] MVP 1 scope reviewed with the client — **carried as C-01**
- [ ] Repo private; no secrets tracked — **partly done** (`.env` untracked via `fix/untrack-env`; repo still public;
      old keys remain in git history but stop working once the Lovable project is deleted — D-14) — **carried as C-02**
- [ ] At least 2 user conversations recorded — **carried as C-03**
- [ ] Client has started WhatsApp verification and the pilot school search — **carried as C-04**
- [x] Sprint 1 written — [`sprint-1.md`](sprint-1.md) (agreement at the kickoff, 19 Oct)

## Review & close-out

**Team review held Mon 6 Oct 2026 (Anne, Herman).** _Closed with four exit criteria not met; each is client- or
interview-dependent rather than team-dependent. They are carried, with owners and dates — not dropped._
The client-facing review of the MVP 1 scope (C-01) happens in the 7–16 Oct window and again at the Sprint 1 demo
on Fri 30 Oct.

### What Sprint 0 delivered

- Product direction confirmed by the client: Tafi is a **parent safety service** — parents get WhatsApp updates
  about their child's trip. Schools are the first customers (D-04, D-05).
- Commercial model decided: **Tafi bills schools, schools bill parents**; pricing is configurable by the client
  (D-06, D-07).
- Architecture decided: **rebuild** as a modular monolith on the team stack; Lovable and the prototype are
  reference material only (D-08, D-09, D-10).
- Delivery window agreed: **3 months, 4 max**, pilot-ready by end of January 2027 (D-11).
- Parent channel decided: **WhatsApp only, no parent app** (D-12).
- MVP 1 scope, roadmap, backlog, risk list and Sprint 1 plan written.

### What was not finished

| ID | Carry-over | Owner | Due | Why it is open |
|---|---|---|---|---|
| C-01 | Client acknowledges the rebuild plan and reviews the MVP 1 scope and `PROPOSED` decisions | Anne | 16 Oct | Needs a client conversation |
| C-02 | Make `annewaithaka/Tafi` private and archive any other copy (D-15); purge `.env` from history (optional once the Lovable project is deleted — D-14) | Herman | 16 Oct | Repo still public; `.env` still in old commits |
| C-03 | At least 2 user conversations (school transport admin, driver, parent) recorded in `ux/ux-research.md`, using [`../ux/interview-guide.md`](../ux/interview-guide.md) | Anne | 16 Oct | Needs access to real users before Term 3 closes |
| C-04 | Client long-lead actions: Meta Business verification + WhatsApp number, pilot school introduction, delete the Lovable project (prototype data already confirmed test-only — D-14) | Client (Anne to chase) | 16 Oct | Client-owned |

### Notes for the close-out

- **C-02 and the exposed keys.** The repo is still public and `.env` (publishable Supabase keys and a Google Maps
  browser key) is still in git history; untracking does not remove a secret. The keys belong to the client's
  Lovable project, which the client confirmed held only test data and no paid services (D-14). Once the client
  deletes that project (C-04) the keys stop working, so purging history becomes optional housekeeping. Making the
  repo private is still required.
- `PROPOSED` rows in [`../product/owner-decisions.md`](../product/owner-decisions.md) are **not** decisions yet.
  The MVP 1 scope in [`../product/mvp-scope.md`](../product/mvp-scope.md) rests on them, so C-01 matters.
- No MVP code was written in Sprint 0. Prototype code in `src/` and `supabase/` was not modified.

## Next sprint

**Sprint 1 (19–30 Oct): UX + Foundation** — full plan in [`sprint-1.md`](sprint-1.md).
Wireframes for the MVP 1 flows; repo layout, Docker Compose and CI; technical spikes (driver location, maps/ETA,
worker choice); WhatsApp message templates drafted.
