# Homework — Sprint 4

> Sprint 4 (the crew trip app) was built and verified on 16 Oct 2026. Source:
> [`../docs/sprints/sprint-4.md`](../docs/sprints/sprint-4.md) and
> [`../docs/delivery/sprint-4.md`](../docs/delivery/sprint-4.md).

## Anne and Herman

### H4-1 — Walk the crew app on a real phone (S4-10)

- **Left over:** the crew screens were verified in a desktop browser. This app is phone-only in practice, and the
  Sprint 3 phone check (H3-4) is still owed too.
- **Why it matters:** marking children one-handed, on a phone, is the whole job; the stopped-confirmation and the
  location permission are both phone behaviours.
- **Next action:** open `http://<laptop-ip>:<WEB_PORT>/crew` on an Android phone on the same network, run a trip,
  and fix anything too small to tap or that overflows.
- **Tracked:** S4-10, MVP-19.

### H4-2 — Confirm the two decisions taken during the build

- **Left over:** **D-32** (a driver working alone confirms "I am stopped", enforced server-side with a 120-second
  window) and **D-33** (location sharing ships inside Sprint 4) were taken by the team so the sprint could
  proceed. Both are flagged in [`../docs/DECISIONS.md`](../docs/DECISIONS.md).
- **Why it matters:** D-32 is a safety rule and D-33 changes what Sprint 5 can promise. Neither should stay a
  team call by default.
- **Next action:** the project lead confirms or changes them; if D-32 changes mechanism, the only file to touch is
  `backend/app/services/trips.py`.
- **Tracked:** D-32, D-33.

## Herman

### H4-3 — Open the pull requests and merge

- **Left over:** Sprints 1–4 sit on two branches; PR #4 (Sprint 0) has been open since 6 October.
- **Why it matters:** four sprints of unreviewed work now.
- **Next action:** open the pull requests, review, and land them.
- **Tracked:** [`../docs/CONTRIBUTING.md`](../docs/CONTRIBUTING.md).

## Notes for the next sprint

- Sprint 5 (parent WhatsApp and the dashboard) can now read `boarding_events` and `trip_locations` directly; the
  `can_message(guardian)` check already exists in `backend/app/services/consent.py`.
- Location trails have gaps by design (T1-11). "Bus approaching" must tolerate a trip whose trail stopped.
