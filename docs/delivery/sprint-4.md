# Sprint 4 Delivery — The Crew Trip App

> Built and verified 16 Oct 2026. For whoever opens the app next. What to run, what to click, what to expect, and
> what is deliberately missing.

## 1. Open it

```sh
docker compose up -d
docker compose exec api alembic upgrade head        # 0003 → 0004_crew_trips
```

Web <http://localhost:5180> (or `WEB_PORT`), API <http://localhost:8010> (or `API_PORT`).

## 2. The walkthrough — about ten minutes

You need a school with a route, a vehicle, a driver and a child on the route. The Sprint 3 walkthrough in
[`sprint-3.md`](sprint-3.md) sets that up; then invitation links for crew come back in the API response in `local`.

| # | Do this | You should see |
|---|---|---|
| 1 | Sign in as the **driver** | You land on `/crew` — "Morning, …", and the runs you are on today |
| 2 | Press **Start this trip** | The trip opens: the route, the vehicle, and every child expected, each marked *pending* |
| 3 | Try **On** for a child without confirming | Refused — a driver working alone must confirm the vehicle is stopped (409) |
| 4 | Press **I am stopped**, then **On** | The child flips to *boarded*; the button state follows |
| 5 | Press **Start sharing** and allow location | "Location sent." and a count of updates; keep this screen open |
| 6 | Press **Off**, then **End this trip** | The trip completes and the summary shows boarded / dropped off / absent |
| 7 | Try to mark anyone after it ends | Refused (409) |
| 8 | Invite a **conductor** onto the same run, sign in as them | No "Are you stopped?" step — a conductor marks without it |

## 3. What each route does

| Route | Who | What it is |
|---|---|---|
| `/crew` | Crew (driver or conductor) | Today's trips for the runs you are on |
| `/crew/trips/:id` | Crew on that trip | Mark children, confirm stopped, share location, end the trip |

API: everything under `/api/v1/crew`, guarded by the `Crew` dependency. Wrong school → **404**; a school admin
→ **403**.

## 4. What is real, and what is not

**Real, and verified:** a trip starts and ends only through valid transitions; boarded / dropped off / absent
persist with the crew membership and the method (`manual`); a second boarding, a drop-off without a boarding, an
absent after any other state, an event on a finished trip and a child who is not on the route are all refused by
the API; location is stored against the trip; another school's crew cannot reach the trip.

**Not real — do not demo these as working:**

- **Nothing is sent to parents.** A trip records events for Sprint 5 to deliver (D-18).
- **Location has gaps.** A phone browser stops sending when the screen locks, so a trail is incomplete by design
  (T1-11, D-33). Nothing downstream may treat it as continuous.
- **The stopped confirmation is a human acknowledgement**, not a motion sensor (D-32).
- **Checked at a phone viewport (390 × 844), not yet on a real device.** Both crew screens fit and are tap-sized;
  permission prompts and the stopped confirmation still need a real phone. Nothing is deployed.
- Card scanning (D-24), live trip view for the school (MVP-15) and billing are later sprints.

## 5. How it was built

| Layer | Where |
|---|---|
| Tables | `backend/alembic/versions/0004_crew_trips.py` — `trips`, `boarding_events`, `trip_locations`; models in `backend/app/models/trip.py` |
| Rules | `backend/app/services/trips.py` — trip lifecycle, event rules, the stopped window |
| Endpoints | `backend/app/api/routes/crew_trips.py` |
| Screens | `frontend/src/routes/crew/`, `frontend/src/components/crew-shell.tsx` |
| Tests | `backend/tests/test_crew_trips.py` (12) — 126 backend tests in total |

## 6. Where Sprint 4 left off

- A real-phone check of the crew screens (S4-10) is outstanding, and matters more here than anywhere: this app is
  meant for a phone.
- D-32 (how a lone driver proves the vehicle is stopped) and D-33 (location inside Sprint 4) were taken by the team
  and are flagged for the project lead to confirm.
- Sprint 4's pull request and review, like Sprints 1–3, are still open.
