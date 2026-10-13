# MVP 1 Wireframes (Anne, Sprint 1)

> Status: **DELIVERED 9 Oct 2026** (T1-01, T1-02). High-fidelity wireframes for the four MVP 1 experiences.
> Not yet reviewed by the client — that is T1-05 / carry-over C-01.

## Where the artifact lives

| | |
|---|---|
| File | [`frontend/public/wireframes/tafi-mvp1-wireframes.html`](../../frontend/public/wireframes/tafi-mvp1-wireframes.html) |
| In the running app | <http://localhost:5173/wireframes/tafi-mvp1-wireframes.html> (plus a browsable gallery at `/wireframes`) |
| Open directly | double-click the file, or drag it into a browser tab |
| Also exported | a PDF sits outside the repo alongside the client's copy |

It is a single self-contained HTML bundle (~2.7 MB) holding all eleven screens stacked vertically, each preceded
by its heading. It needs JavaScript and an internet connection is not required. It is kept under `frontend/public/`
so the same file can be opened straight from disk **and** served by the app, with one copy rather than two.

## The screens

| # | Screen | What it shows | MVP 1 items |
|---|---|---|---|
| 1 | School portal · Today | Morning run board: children riding, trips running, boarded, not boarded; the trip table with status per route; "Needs attention" for delays, no-shows and failed messages; messages-sent counter | MVP-15, MVP-14 |
| 2 | School portal · Children & guardians | Riders table with route, stop, guardian and WhatsApp opt-in state; import spreadsheet; send WhatsApp invites; guardian detail panel with morning and afternoon stops | MVP-04, MVP-05, MVP-08 |
| 3 | School portal · Routes, vehicles & crew | Routes with their stops, the vehicles and the driver/conductor assigned to each | MVP-06, MVP-07 |
| 4 | School portal · Trip detail | One trip: the route, its stop order, who boarded where and the timeline of events | MVP-10, MVP-15 |
| 5 | Crew app · My trip today | The driver's day: today's trip, start and end controls, and the children expected at each stop | MVP-09 |
| 6 | Crew app · Mark children on and off | Tapping each child boarded, dropped off or absent, one-handed on a phone | MVP-10, MVP-11 |
| 7 | Crew app · Trip complete | Summary after the trip and what was recorded | MVP-10 |
| 8 | Parent · WhatsApp messages (Option A) | The message designs: boarded, approaching, dropped off, absent, and the failure case | MVP-12, MVP-13, T1-03 |
| 9 | Parent · Registration page from invite link (Option A) | What a guardian sees when the school invites them, including the consent moment | MVP-05, owner-decision row 9 |
| 10 | Parent · Web dashboard (Option B) | A parent web view of their child's trips | **Not in MVP 1** — needs owner-decision row 9 |
| 11 | Operator · Overview | A transport operator running several schools | LATER-04 (after MVP 1) |

## What the wireframes add to the plan

- The school portal sidebar shows **Trips**, **Message log** and **Settings** sections. Message log maps to MVP-14;
  **Trips** and **Settings** are not in the MVP 1 backlog yet — carried into [`homework/`](../../homework/README.md).
- The parent section deliberately shows **Option A (WhatsApp + a registration page)** and **Option B (a parent web
  dashboard)** side by side. D-12 says WhatsApp only, so Option B is an open question for the client
  (owner-decision row 9), not a commitment.
- Screen 8 is the closest thing to the WhatsApp templates T1-03 asks for, but it is a design, not approved copy.

## Updating it

The deck is an export, not hand-written source. Edit the design in the tool it came from, re-export the HTML, and
replace this one file — then re-run the screen list above if screens were added or renamed. Keep the file
self-contained so it keeps working from disk.
