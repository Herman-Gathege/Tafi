# Tafi Status

_Last updated: 14 Oct 2026_

**Phase:** Sprint 4 — Crew Trip App built and verified (16 Oct 2026). **Sprint 5 — Parent WhatsApp + Dashboard is
next.** A real-phone check and the pull requests are outstanding.

**Current objective:** Walk the crew app on a real phone, get Sprints 1–4 reviewed and merged, and get the client
moving on Meta verification, staging and the consent wording.

## Where the product is

Tafi is a parent safety service for school transport: parents get WhatsApp updates when their child boards, when
the bus is approaching and when they are dropped off, and can also check a parent web dashboard. Schools are the
first customers. The product is built from scratch on the team stack; the client's Lovable prototype is archived
at tag `prototype-lovable-2026-07`.

**You can open the app today.** Walk through it with [`delivery/sprint-3.md`](delivery/sprint-3.md) (Sprint 2's
accounts walkthrough is [`delivery/sprint-2.md`](delivery/sprint-2.md)).

## Decided (see [`DECISIONS.md`](DECISIONS.md))

- The client is the product owner; Anne and Herman are the developers.
- Tafi is a **parent safety service**: parents get WhatsApp updates about their child's trip.
- **MVP 1 serves schools.** Other transport providers come later; the data model allows for them.
- Billing: **Tafi bills schools; schools bill parents** for transport.
- Platform pricing is **configurable by the client** without developers; KES 450/child/month is a placeholder.
- **Rebuild on the team stack** (FastAPI · React · PostgreSQL · Redis · Docker · DigitalOcean). Lovable is not used.
- Delivery window: **3 months, 4 max** → pilot-ready by end of January 2027.
- Parents get **WhatsApp messages and a parent web dashboard** (D-20). Parents sign in with a one-time code on
  WhatsApp; the dashboard lands in Sprint 5.
- **Crew:** driver required, conductor optional; a driver alone marks only when stopped (D-21).
- **Guardian registration both ways**, and no messages before consent (D-22). Consent wording is versioned and
  still a **draft** awaiting the client (D-27).
- **Wireframes approved** by the client (D-23). **Child ID cards** later; the data is prepared (D-24).
- Other schools' records are reported as missing (D-26); route changes take effect today (D-28); guardians change
  their number through the school (D-29); roster import is all or nothing (D-30).
- A session is a **12-hour JWT in an httpOnly cookie** (D-17); invite links come back in the API response **in
  `local` only** until the notification worker exists (D-18).

## Built so far

| Area | State |
|---|---|
| Accounts | Sign in, sign out, invite, accept invite, forgot and reset password |
| Roles | Tafi staff; `school_admin`, `driver` and `conductor` memberships |
| Tenancy | Every route resolves the caller's school; other schools' rows are 404 (D-26) |
| Onboarding | `/app/admin`: list schools, create a school, invite its first admin |
| Children & guardians | `/app/children`: search, filters, add a child, guardians, emergency contacts, routes and stops, send links, paper consent, spreadsheet import |
| Routes & crew | `/app/routes`: routes, ordered stops, morning and afternoon runs, vehicles, crew invites |
| Stop requests | `/app/requests`: approve or decline guardians' stop changes |
| Guardian registration | `/guardian-invite?token=…`: confirm details, consent, second guardian, emergency contact, stop request |
| Crew trip app | `/crew`: today's trips, start/end, boarded / dropped off / absent with who and how, the driver-alone stopped rule (D-32), and location sharing (D-33) |
| `backend/` | FastAPI, four Alembic migrations, Celery worker; ruff, mypy and **126 tests** pass |
| `frontend/` | React + Vite + Tailwind; ESLint and TypeScript pass |
| Local stack | `docker compose up` runs api + db + redis + worker + web |
| CI | GitHub Actions on backend and frontend |
| Data model | [`architecture/data-model.md`](architecture/data-model.md) |

Nothing is deployed, and nothing sends WhatsApp or email yet.

## Homework (what is left)

The live list is in [`../homework/`](../homework/README.md). In short:

- **Client:** Meta Business verification and a WhatsApp number (blocks S3-12 and Sprint 5); approve the consent
  wording and name a privacy contact; a DigitalOcean account, domain and database choice for staging; which parent
  messages ship first; the real price; a pilot school; deleting the Lovable project.
- **Herman:** open the pull requests for Sprints 1–3 and land PR #4; review Sprint 3; hardening (Sprint 7); make
  `annewaithaka/Tafi` private (C-02).
- **Anne:** check the new screens on a real phone; the design review of the Sprint 2 screens (S2-07); WhatsApp
  template copy (S3-12) and the Cloud API spike (T1-15); two user conversations (C-03).

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Meta Business verification not started | WhatsApp templates cannot be submitted; Sprint 5 slips | The most urgent client item; raise it now |
| Consent wording not approved | The pilot cannot start messaging lawfully | Client approves the draft and names a privacy contact (H3-1) |
| Three sprints unmerged and unreviewed | Problems surface late, and the branch keeps growing | Herman opens the pull requests (H2-2, H3-3) |
| Parent dashboard adds scope (D-20) | Sprint 5 is the shortest sprint before the holiday | WhatsApp messages first; the dashboard can move into January ahead of billing |
| `annewaithaka/Tafi` is still public | The client's code is readable by anyone | C-02 |
| Nothing is deployed | The client cannot see progress without running Docker | Staging is ready to deploy once the client provides an account |
| School calendar: Term 3 closes late Oct/early Nov | No one to interview or pilot with over the holidays | User conversations still owed (C-03); pilot in Term 1 2027 |
| Children's personal data (Kenya Data Protection Act 2019) | Legal and trust risk | Consent before messaging (D-22, D-27); minimum data; privacy checklist is MVP-22 |

## Next

Sprint 4 (crew trip app: today's trips, start and end, boarded / dropped off / absent, location) → Sprint 5
(parent WhatsApp and dashboard). Deploy staging once the client provides an account.
