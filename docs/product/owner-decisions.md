# Client Decisions

> Decisions the **client** (product owner) makes. Status: `DECIDED` · `PROPOSED` (team recommendation awaiting
> client confirmation) · `OPEN` (not yet discussed). Decided items are copied into [`../DECISIONS.md`](../DECISIONS.md).

| # | Decision | Answer / recommendation | Status | Ref |
|---|---|---|---|---|
| 1 | Product direction | Parent safety service via WhatsApp | DECIDED | D-04 |
| 2 | Who pays | Transport providers: schools in MVP 1, other providers later | DECIDED | D-05 |
| 3 | Billing model | Tafi bills schools; schools bill parents for transport | DECIDED | D-06 |
| 4 | Platform pricing | Client-configurable in the app; KES 450/child/month placeholder | DECIDED | D-07 |
| 5 | Parent channel | WhatsApp only, no app | DECIDED | D-12 |
| 6 | Rebuild plan | Rebuild on team stack before the first school uses Tafi (~1 extra month at the start) | PROPOSED — client acknowledgement pending | D-08 |
| 7 | Parent messages in MVP 1 | Trip started · boarded · bus approaching · dropped off · absent | PROPOSED | — |
| 8 | Driver workflow | Driver uses a phone web app: start trip, tap each child boarded/dropped off, share location during the trip | PROPOSED | — |
| 9 | "Bus approaching" definition | Message when the bus is ~5 minutes (or a set distance) from the child's stop; threshold adjustable per school | PROPOSED | — |
| 10 | School fee tracking (school → parent) | In MVP 1 as terms, invoices and manually recorded payments; may move after the pilot if time is tight | PROPOSED | — |
| 11 | How Tafi charges schools | Unit (per child/month vs per term vs per bus), invoicing frequency, free pilot period | OPEN | — |
| 12 | Payment collection | Manual recording in MVP 1; M-Pesa automation later | PROPOSED | — |
| 13 | Guardian consent | Schools collect guardian consent for WhatsApp messages; Tafi records it | PROPOSED | — |
| 14 | Data protection | Kenya Data Protection Act 2019 baseline; confirm client registration obligations with the ODPC | OPEN | — |
| 15 | Pilot school | Client introduces at least one candidate school | OPEN | — |
| 16 | Pilot timing | Term 1 2027, from February | PROPOSED | D-11 |
| 17 | WhatsApp sender | Client-owned Meta Business account and dedicated phone number | PROPOSED | — |
| 18 | Success metric | e.g. % of trips where every guardian got a "boarded" message | OPEN | — |

## How to use this page

1. Anne takes `PROPOSED` and `OPEN` rows to the client.
2. Once answered, set `DECIDED`, add the decision to `DECISIONS.md` with the next ID, and reference it here.
3. Rows 6, 11 and 15 are the most urgent for Sprint 1.
