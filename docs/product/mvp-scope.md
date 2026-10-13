# Tafi MVP 1 Scope (schools)

> Built around the parent safety promise (D-04), sold to schools (D-05). **Prototype code ≠ requirement.**
> Sprint numbers refer to [`../sprints/roadmap.md`](../sprints/roadmap.md). Screens follow the approved wireframes
> (D-23), described in [`../ux/wireframes.md`](../ux/wireframes.md).

## Must have

- Tafi platform admin onboards a school and its first admin.
- Sign in, invite/accept, password reset; roles: platform admin, school admin, driver, conductor (D-21).
- Students and guardians (more than one guardian per student; WhatsApp numbers in E.164); emergency contact.
- Guardian registration both ways (D-22): the school enters the child and guardians; each guardian confirms through
  an invite link, adds a second guardian or emergency contact, and gives consent. No messages before consent.
- Routes with ordered stops; vehicles; crew (driver required, conductor optional per route run); assignments of
  children to pickup and drop-off stops.
- Crew phone web app: today's trips, start/end trip, mark boarded / dropped off / absent, share location. Used by
  whoever is crew; a driver alone can only mark while stopped (D-21). Each event records who marked it and how.
- Parent WhatsApp messages: trip started, boarded, bus approaching, dropped off.
- Notification log with delivery status and retries.
- Clear feedback on every action; mobile-first screens.

## Should have

- Parent web dashboard (D-20): child status, today's trip, mark absent, contact the school, guardians and alerts.
  Sign-in with a one-time code sent to the guardian's WhatsApp number.
- Guardian stop-change requests, approved by the school (D-22).
- CSV import of students and guardians (fast onboarding).
- School admin live trip view (which children are on which bus now).
- School → parent fees: terms, invoices, manually recorded payments.
- Platform plans and pricing editable by the client.
- Tafi → school invoices from configured pricing (manual collection).

## Could have

- Route map with stop ordering on a map.
- SMS fallback when WhatsApp fails.
- Simple reports (trips, notifications delivered, outstanding fees).

## Not now

- Child ID card scanning (QR or NFC). The data model is prepared for it in Sprints 3–4 (D-24).
- Independent transport providers and the operator portal (later scope, D-05; overview wireframe exists).
- Native parent mobile app (the parent dashboard is a web app, D-20).
- M-Pesa automation.
- GPS hardware / telematics.
- Advanced analytics.
- Syncing attendance with the school's own system.

## Feature table

| Feature | User | Problem solved | Priority | Sprint | Prototype has it? |
|---|---|---|---|---|---|
| School onboarding by Tafi admin | Platform admin | Schools can start using Tafi | Must | 2 | Broken (first-school dead-end) |
| Auth: sign in, invite, reset | All staff | Controlled access, recovery | Must | 2 | Partial (no reset) |
| Conductor role | School admin | Vehicles with a conductor can use one | Must | 3 | No |
| Students, guardians, emergency contacts | School admin | Know who travels and who to notify | Must | 3 | Partial (one guardian, no consent) |
| Guardian invite link, confirmation and consent | Guardian | Correct numbers; lawful messaging | Must | 3 | No |
| Routes, stops, vehicles, crew | School admin | Run the fleet | Must | 3 | Partial (stops unused) |
| Child cards table (unused until scanning) | — | Scanning slots in later without rework | Must (data only) | 3 | No |
| Crew trip app + check-in | Driver or conductor | Record boarding and drop-off | Must | 4 | No |
| Live location during trip | Crew → parent | Power "bus approaching" | Must | 4 | No |
| Parent WhatsApp messages | Parent | Peace of mind; fewer calls | Must | 5 | No |
| Notification log | School admin | Prove messages were sent | Must | 5 | No |
| Parent web dashboard + one-time-code sign-in | Parent | See status any time | Should | 5 | No |
| Guardian stop-change requests | Guardian, school admin | Keep stops current | Should | 3 | No |
| CSV import | School admin | Onboard in a day | Should | 3 | No |
| Live trip view | School admin | See buses now | Should | 5 | No |
| School → parent fees | School admin | Track transport fees | Should | 6 | Yes (needs fixes) |
| Configurable platform pricing | Client | Change prices without developers | Should | 6 | No |
| Tafi → school invoices | Client | Get paid | Should | 6 | No |
| Child card scanning | Crew | Faster, verifiable boarding | Later | — | Broken (regenerate) |
| SMS fallback | Parent | Reach parents without WhatsApp | Could | Later | No |

**Scope rule:** do not add a feature just because the prototype or a table has it.

**Scope pressure:** the parent dashboard (D-20) adds work to a fixed window (D-11). If Sprint 5 runs long, the
dashboard ships after WhatsApp messages are working; billing (Sprint 6) remains the release valve.
