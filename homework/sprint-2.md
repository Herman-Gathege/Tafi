# Homework — Sprint 2

> Sprint 2 closed Mon 13 Oct 2026 with seven of eight tasks done. Source:
> [`../docs/sprints/sprint-2.md`](../docs/sprints/sprint-2.md#review--close-out).

## Anne

### H2-1 — Review the new screens against the deck (S2-07)

- **Left over:** sign in, accept invite, forgot password, reset password and the platform admin console were
  designed by Herman during the sprint. Nobody has checked them against the wireframes' tokens, shell and tone.
- **Why it matters:** these are the first screens a real user meets, and they are the only screens in the product
  that the deck does not cover.
- **Next action:** open `/signin`, `/accept-invite`, `/forgot-password` and `/app/admin`, and either approve them or
  list changes. The route map and the walkthrough are in [`../docs/delivery/sprint-2.md`](../docs/delivery/sprint-2.md).
- **Tracked:** S2-07.

## Herman

### H2-2 — Open the pull requests

- **Left over:** Sprint 1 (`feature/sprint-1-foundation`) and Sprint 2 (stacked on the same branch) are pushed with
  green CI, but no pull request is open. PR #4 (the Sprint 0 close-out) is still open too.
- **Why it matters:** two sprints of work are unreviewed, and the branch keeps growing.
- **Next action:** open the pull request against `main`, ask Anne to review, and land PR #4 first.
- **Tracked:** [`../docs/CONTRIBUTING.md`](../docs/CONTRIBUTING.md).

### H2-3 — Authentication hardening

- **Left over:** no refresh tokens (a session simply ends after 12 hours), no CSRF token, no rate limiting or
  lockout on sign-in, and no password-strength rules beyond a minimum length.
- **Why it matters:** acceptable for a pilot on a private URL; not acceptable for a public launch.
- **Next action:** schedule with Sprint 7 (hardening). Until then keep the app off the public internet without a
  decision.
- **Tracked:** D-17, Sprint 7.

### H2-4 — Real delivery for invites and password resets

- **Left over:** the API returns invite and reset links in the response **in `local` only** (D-18). Nothing sends
  email or WhatsApp, so outside local those flows dead-end.
- **Why it matters:** a real school cannot be onboarded without someone receiving a link.
- **Next action:** the notification worker lands in Sprint 5; wire the invite and reset emails there and delete the
  local-only branch.
- **Tracked:** D-18, Sprint 5, T1-03.

## Client

### H2-5 — A DigitalOcean account for staging (C-04)

- **Left over:** the staging configuration and runbook exist
  ([`../docs/architecture/deployment.md`](../docs/architecture/deployment.md)), but nothing is deployed. It needs
  an account, a domain and a decision on the managed database.
- **Why it matters:** the client cannot see progress without running Docker locally, and Sprint 7 (launch) assumes
  staging already exists.
- **Next action:** Anne raises it with the client alongside the Meta verification already owed.
- **Tracked:** C-04, MVP-21.

## Notes for the next sprint

- Sprint 3 builds the school's data (students, guardians with consent, routes and stops, vehicles, drivers,
  assignments, CSV import). Every one of those tables carries `organization_id`, and every route resolves the
  caller's membership first — the pattern is in `backend/app/api/deps.py`.
- The invoice-and-pricing work in Sprint 6 reuses the same membership check, so nothing new is needed for tenancy.
