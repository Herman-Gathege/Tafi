# Tafi MVP 1 Scope (schools)

> Built around the parent safety promise (D-04), sold to schools (D-05). **Prototype code ≠ requirement.**
> Sprint numbers refer to [`../sprints/roadmap.md`](../sprints/roadmap.md).

## Must have

- Tafi platform admin onboards a school and its first admin.
- Sign in, invite/accept, password reset; roles: platform admin, school admin, driver.
- Students and guardians (more than one guardian per student; WhatsApp numbers in E.164); guardian consent record.
- Routes with stops; vehicles; drivers; assignments.
- Driver phone web app: today's trips, start/end trip, mark boarded / dropped off / absent, share location.
- Parent WhatsApp messages: trip started, boarded, bus approaching, dropped off.
- Notification log with delivery status and retries.
- Clear feedback on every action; mobile-first screens.

## Should have

- CSV import of students and guardians (fast onboarding).
- School admin live trip view (which children are on which bus now).
- School → parent fees: terms, invoices, manually recorded payments.
- Platform plans and pricing editable by the client.
- Tafi → school invoices from configured pricing (manual collection).

## Could have

- Route map and stop ordering.
- QR-scan check-in.
- SMS fallback when WhatsApp fails.
- Simple reports (trips, notifications delivered, outstanding fees).

## Not now

- Independent transport providers (later scope, D-05).
- Parent app.
- M-Pesa automation.
- GPS hardware / telematics.
- Advanced analytics.

## Feature table

| Feature | User | Problem solved | Priority | Sprint | Prototype has it? |
|---|---|---|---|---|---|
| School onboarding by Tafi admin | Platform admin | Schools can start using Tafi | Must | 2 | Broken (first-school dead-end) |
| Auth: sign in, invite, reset | All | Controlled access, recovery | Must | 2 | Partial (no reset) |
| Students, guardians, consent | School admin | Know who travels and who to notify | Must | 3 | Partial (one guardian, no consent) |
| Routes, stops, vehicles, drivers | School admin | Run the fleet | Must | 3 | Partial (stops unused) |
| Driver trip app + check-in | Driver | Record boarding and drop-off | Must | 4 | No |
| Live location during trip | Driver → parent | Power "bus approaching" | Must | 4 | No |
| Parent WhatsApp messages | Parent | Peace of mind; fewer calls | Must | 5 | No |
| Notification log | School admin | Prove messages were sent | Must | 5 | No |
| CSV import | School admin | Onboard in a day | Should | 3 | No |
| Live trip view | School admin | See buses now | Should | 5 | No |
| School → parent fees | School admin | Track transport fees | Should | 6 | Yes (needs fixes) |
| Configurable platform pricing | Client | Change prices without developers | Should | 6 | No |
| Tafi → school invoices | Client | Get paid | Should | 6 | No |
| QR check-in | Driver | Faster boarding | Could | Later | Broken (regenerate) |
| SMS fallback | Parent | Reach parents without WhatsApp | Could | Later | No |

**Scope rule:** do not add a feature just because the prototype or a table has it.
