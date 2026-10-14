# Sprint 3 Delivery — The School's Data

> Closed 14 Oct 2026. For whoever opens the app next — a developer, Anne, Herman, or the client in a demo. What to
> run, what to click, what to expect, and what is deliberately missing.

## 1. Open it

From the repository root, in PowerShell or a terminal:

```sh
docker compose up --build -d
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m app.cli create-platform-admin --email you@example.com --password "choose-something-long" --name "Your Name"
```

Open the web port from `.env` (`WEB_PORT`, default <http://localhost:5173>).

**If you moved the ports** because another project uses 5173 or 8000, set these three together in `.env`, or
sign-in fails with "Cannot reach the Tafi API" and invite links point at the wrong place:

```
VITE_API_BASE_URL=http://localhost:<API_PORT>
CORS_ORIGINS=http://localhost:<WEB_PORT>
APP_PUBLIC_URL=http://localhost:<WEB_PORT>
```

Then `docker compose up -d --force-recreate web api`.

Use made-up phone numbers only, such as `0700 000 001`.

## 2. The walkthrough — about fifteen minutes

Open each invite link in a **private window**, so you stay signed in as the school admin in the main one.

| # | Do this | You should see |
|---|---|---|
| 1 | Sign in as the platform admin; add "Riverside Academy"; invite a school admin; accept it | You land in the school portal with **Children & guardians**, **Routes & crew** and **Stop requests** in the menu |
| 2 | **Routes & crew → New route**: code `R1`, area "Kileleshwa" | The route card appears and opens below |
| 3 | Add stops "Main gate", "Shops", "Church"; move "Church" up with ↑ | Numbered in the new order |
| 4 | Add vehicle `kda 213a`, 26 seats | It shows as `KDA 213A` |
| 5 | Invite a driver and a conductor; accept both invites | Both listed under Crew with their role |
| 6 | Set the **morning run**: 06:30, the vehicle, the driver, no conductor | Saves; the driver list only offers drivers |
| 7 | **Children & guardians → Add child**, guardian number `0700 000 001` | The child appears; WhatsApp shows **Not confirmed** |
| 8 | Open the child; **Put on a route**: R1, pickup "Main gate" | "R1 · Main gate" in the list |
| 9 | Add a sibling with the same guardian number | Both children share one guardian |
| 10 | On the guardian, **Send link**; open it | The registration page: school name, the children, their stops, the consent text |
| 11 | Ask for a different stop, tick consent, confirm | "You're all set". Back in the portal the guardian shows **Opted in** |
| 12 | **Stop requests**: approve with the new stop | The child's stop changes; the count in the menu clears |
| 13 | **Import spreadsheet → Download the template**, import it unchanged | 2 children added on R1; the import refuses a file with any bad row and lists the rows |
| 14 | Sign in as the driver | No school screens; the API refuses them too |

## 3. Routes

| Route | Who | What it is |
|---|---|---|
| `/app/children` | School admin | Children, guardians, emergency contacts, routes and stops, links, consent, import |
| `/app/routes` | School admin | Routes, stops, runs, vehicles, crew |
| `/app/requests` | School admin | Guardians' stop-change requests |
| `/guardian-invite?token=…` | Anyone with the link | A guardian confirms their details and consents |

Every school endpoint is under `/api/v1/school/…`; the guardian's are under `/api/v1/guardian-invites/…`. The API
docs page lists them all.

## 4. What is real, and what is not

**Real, and verified:**

- Everything in the walkthrough, against the running stack; 114 backend tests; ESLint and TypeScript.
- One school never sees another's data; other schools' records are reported as missing (D-26).
- No guardian can be messaged without a current consent: `can_message(guardian)` is ready for Sprint 5 (D-27).

**Not real yet — do not demo these as working:**

- **Nothing sends WhatsApp or email.** Guardian and staff links appear on screen only in `local` (D-18).
- **The consent wording is a draft** awaiting the client and a privacy contact (D-27).
- **No trips.** The crew app, boarding and location are Sprint 4; the Today page is still a placeholder.
- **Not checked on a real phone yet**, and **nothing is deployed**.

## 5. How it was built

| Layer | Where |
|---|---|
| Tables | `backend/alembic/versions/0003_school_operations.py`, `backend/app/models/{student,guardian,transport,mixins}.py`; described in [`../architecture/data-model.md`](../architecture/data-model.md) |
| Access checks | `backend/app/api/deps.py` |
| Endpoints | `backend/app/api/routes/school_{students,transport,crew,guardians,import}.py`, `guardian_invites.py` |
| Rules | `backend/app/services/consent.py`, `backend/app/services/roster_import.py`, `backend/app/schemas/common.py` (phone numbers) |
| Screens | `frontend/src/routes/school/`, `frontend/src/routes/guardian-invite.tsx` |
| Tests | `backend/tests/test_school_*.py`, `test_guardian_invites.py`, `test_roster_import.py`, `test_phone_numbers.py` |
