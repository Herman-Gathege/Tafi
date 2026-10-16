# MVP 1 Wireframes (Anne, Sprint 1)

> Status: **DELIVERED 9 Oct 2026** (T1-01, T1-02) and **APPROVED by the client 14 Oct 2026** (D-23) as the design
> baseline. Screens 2, 3 and 9 were built in Sprint 3; see the table below.

## Where the artifact lives

| | |
|---|---|
| File | [`frontend/public/wireframes/tafi-mvp1-wireframes.html`](../../frontend/public/wireframes/tafi-mvp1-wireframes.html) |
| In the running app | `/wireframes/tafi-mvp1-wireframes.html` on the web port (plus a browsable gallery at `/wireframes`) |
| Open directly | double-click the file, or drag it into a browser tab |
| Also exported | a PDF sits outside the repo alongside the client's copy |

It is a single self-contained HTML bundle (~2.7 MB) holding all eleven screens stacked vertically, each preceded
by its heading. It needs JavaScript; an internet connection is not required. It is kept under `frontend/public/`
so the same file can be opened straight from disk **and** served by the app, with one copy rather than two.

## The screens

| # | Screen | What it shows | MVP 1 items | Built |
|---|---|---|---|---|
| 1 | School portal · Today | Morning run board; trip table; "Needs attention"; messages-sent counter | MVP-15, MVP-14 | Sprint 5 (needs trips and messages) |
| 2 | School portal · Children & guardians | Riders table with route, stop, guardian and WhatsApp state; import spreadsheet; send WhatsApp invites; child detail panel | MVP-04, MVP-05, MVP-08 | ✅ Sprint 3 — `/app/children` |
| 3 | School portal · Routes, vehicles & crew | Routes with their stops, the vehicles and the driver/conductor assigned to each | MVP-06, MVP-07 | ✅ Sprint 3 — `/app/routes` |
| 4 | School portal · Trip detail | One trip: stop order, who boarded where, the timeline | MVP-10, MVP-15 | Sprint 4–5 |
| 5 | Crew app · My trip today | Today's trip, start and end, the children expected at each stop | MVP-09 | Sprint 4 |
| 6 | Crew app · Mark children on and off | Tapping each child boarded, dropped off or absent, one-handed on a phone | MVP-10, MVP-11 | Sprint 4 |
| 7 | Crew app · Trip complete | Summary after the trip | MVP-10 | Sprint 4 |
| 8 | Parent · WhatsApp messages | Boarded, approaching, dropped off, absent, delay, and the failure case | MVP-12, MVP-13, S3-12 | Sprint 5 (copy needs the client) |
| 9 | Parent · Registration page from invite link | Confirm details, consent, second guardian, emergency contact, stop request | MVP-05, MVP-23 | ✅ Sprint 3 — `/guardian-invite?token=…` |
| 10 | Parent · Web dashboard | A parent web view of their child's trips | MVP-25, MVP-26 — **in MVP 1** since D-20 | Sprint 5 |
| 11 | Operator · Overview | A transport operator running several schools | LATER-04 (after MVP 1) | — |

## Differences between the wireframes and the build

- The app keeps Herman's **top navigation** rather than the wireframes' sidebar; the colours, type, cards and
  status pills follow the wireframes.
- **Stop requests** (`/app/requests`) is a screen the wireframes did not draw; it handles the stop-change requests
  guardians make from screen 9 (D-22).
- The sidebar's **Trips**, **Message log** and **Settings** arrive with Sprints 4 and 5; Settings is not in the MVP 1
  backlog yet.

## Updating it

The deck is an export, not hand-written source. Edit the design in the tool it came from, re-export the HTML, and
replace this one file — then update the screen list above if screens were added or renamed. Keep the file
self-contained so it keeps working from disk.
