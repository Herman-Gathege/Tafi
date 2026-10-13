# Sprint 2 Delivery — Accounts, Roles and School Onboarding

> Closed Mon 13 Oct 2026. This page is for whoever opens the app next — a developer, Anne, or the client in a demo.
> It says what to run, what to click, what to expect, and what is deliberately missing.

## 1. Open it

From the repository root:

```sh
make up                                   # build and start api + db + redis + worker + web
docker compose exec api alembic upgrade head
docker compose exec api python -m app.cli create-platform-admin \
  --email you@example.com --password "choose-something-long" --name "Your Name"
```

Then open the URL for `WEB_PORT` in `.env` (the default is <http://localhost:5173>; on this machine it is
<http://localhost:5180>). The API is on `API_PORT` — <http://localhost:8000/docs> lists every endpoint.

There is no self-signup. The CLI exists because the first Tafi account has to come from somewhere.

## 2. The walkthrough — about ten minutes

| # | Do this | You should see |
|---|---|---|
| 1 | Open `/` | The public landing page. Anyone can look; nothing is gated. |
| 2 | Open `/wireframes` | Anne's eleven screens, with a jump bar. Also public. |
| 3 | Sign in at `/signin` as the platform admin | You land on `/app/admin`, the platform console |
| 4 | Add a school — "Riverside Academy" | It appears under Schools |
| 5 | Press **Invite an admin**, give an email | The invitation is created and, in `local`, the response includes the invite link |
| 6 | Copy the invite link into a private window | The page names the school and the invited email |
| 7 | Set a name and password there | You are signed in as that school admin and land on `/app`, headed with the school name |
| 8 | Sign out, then sign in as the school admin | Same portal; the **Platform admin** tab is gone |
| 9 | Sign out, sign in as the platform admin, and try to open `/app/admin` as the school admin | You are bounced back to `/app` — the API refuses the platform routes with `403` |
| 10 | Use **Forgot your password** | The same message whatever the address; in `local` the reset link is shown so the flow can be finished |
| 11 | Open the reset link twice | The first works; the second says the link is no longer valid |

## 3. What each route does

| Route | Who | What it is |
|---|---|---|
| `/` | Anyone | Landing page |
| `/wireframes` | Anyone | The MVP 1 wireframe deck, with a jump bar |
| `/signin` | Anyone | Sign in |
| `/accept-invite?token=…` | Anyone with the link | Sets up the account an invitation was for |
| `/forgot-password` | Anyone | Asks for a reset link |
| `/reset-password?token=…` | Anyone with the link | Chooses a new password |
| `/app` | Signed-in | The school portal — a placeholder until Sprint 3 |
| `/app/admin` | Tafi staff | List schools, add one, invite its first admin |

## 4. What is real, and what is not

**Real, and verified against the running stack:**

- Sign in, sign out, invite, accept invite, forgot password, reset password.
- Roles: Tafi staff (`is_platform_admin`) and school staff (`school_admin`, `driver`).
- Tenancy: the API resolves the caller's organization before touching data, refuses platform routes to school
  admins with `403`, and only ever returns a school admin their own school.
- Sessions: a 12-hour JWT in an httpOnly cookie. JavaScript cannot read it, and the browser does send it back
  (checked in a real browser, not only with curl).
- 24 backend tests, ruff, mypy, and the frontend lint, typecheck and build.

**Not real yet — do not demo these as working:**

- **Nothing sends email or WhatsApp.** Invite and reset links come back in the API response *only when
  `APP_ENV=local`*; any other environment returns no link, deliberately (D-18). Real delivery arrives with the
  notification worker in Sprint 5.
- **No school data.** Students, guardians, routes, stops, vehicles and drivers are Sprint 3.
- **No driver landing page.** A driver can be invited and the role is stored, but the crew app is Sprint 4.
- **No refresh tokens, CSRF token, sign-in rate limiting or lockout.** A session simply ends after 12 hours
  (D-17). Fine for a pilot behind a private URL; not fine for a public launch.
- **Nothing is deployed.** The staging configuration and runbook are ready, but they need the client's
  DigitalOcean account.

## 5. How it was built

| Layer | Where |
|---|---|
| Accounts, sessions, invites, resets | `backend/app/api/routes/auth.py`, `backend/app/core/security.py` |
| Roles and tenant resolution | `backend/app/api/deps.py`, `backend/app/models/user.py` |
| School onboarding | `backend/app/api/routes/organizations.py` |
| Schema | `backend/alembic/versions/0002_auth_and_tenancy.py` |
| First-account CLI | `backend/app/cli.py` |
| Screens | `frontend/src/routes/{signin,accept-invite,forgot-password,reset-password,admin}.tsx` |
| Session in the client | `frontend/src/lib/session.ts`, `frontend/src/components/require-auth.tsx` |
| Tests | `backend/tests/test_auth.py`, `backend/tests/test_tenancy.py` |

Two decisions shaped it: a session is an httpOnly cookie rather than a token in JavaScript (D-17), and invite and
reset links are surfaced locally so the flows are demonstrable before any delivery channel exists (D-18).

## 6. Where Sprint 2 left off

- Anne still owes a design review of the five new screens (S2-07).
- The branch is pushed with green CI but no pull request is open.
- Sprint 3 starts on the school's data; every table it adds carries `organization_id` and every route resolves the
  caller's membership first, the pattern established here.

The full leftover list is [`../../homework/sprint-2.md`](../../homework/sprint-2.md).
