# Client Decisions

> Decisions the **client** (product owner) makes. Status: `DECIDED` · `PROPOSED` (team recommendation awaiting
> client confirmation) · `OPEN` (not yet discussed). Decided items are copied into [`../DECISIONS.md`](../DECISIONS.md).

| # | Decision | Answer / recommendation | Status | Ref |
|---|---|---|---|---|
| 1 | Product direction | Parent safety service via WhatsApp | DECIDED | D-04 |
| 2 | Who pays | Transport providers: schools in MVP 1, other providers later | DECIDED | D-05 |
| 3 | Billing model | Tafi bills schools; schools bill parents for transport | DECIDED | D-06 |
| 4 | Platform pricing | Client-configurable in the app; KES 450/child/month placeholder | DECIDED | D-07 |
| 5 | Parent channel | WhatsApp for every parent, **plus** an optional parent web dashboard (Option B) | DECIDED (14 Oct) | D-20 (supersedes D-12) |
| 6 | Rebuild plan | Rebuild on team stack before the first school uses Tafi | PROPOSED — client acknowledgement pending | D-08 |
| 7 | Parent messages in MVP 1 | Trip started · boarded · bus approaching · dropped off · absent; also left school, delay, and the nightly "riding tomorrow?" check shown in the wireframes | PROPOSED — client to pick the first set | — |
| 8 | Crew workflow | Driver required, conductor optional; whoever is crew marks children in a phone web app; a driver alone marks only when stopped | DECIDED (14 Oct) | D-21 |
| 9 | "Bus approaching" definition | Message when the bus is ~5 minutes (or a set distance) from the child's stop; threshold adjustable per school | PROPOSED | — |
| 10 | School fee tracking (school → parent) | In MVP 1 as terms, invoices and manually recorded payments; may move after the pilot if time is tight | PROPOSED | — |
| 11 | How Tafi charges schools | Unit (per child/month vs per term vs per bus), invoicing frequency, free pilot period | OPEN | — |
| 12 | Payment collection | Manual recording in MVP 1; M-Pesa automation later | PROPOSED | — |
| 13 | Guardian registration and consent | Both ways: the school enters guardians, guardians confirm and consent through a link; no messages before consent | DECIDED (14 Oct) | D-22 |
| 14 | Data protection | Kenya Data Protection Act 2019 baseline; confirm client registration obligations with the ODPC | OPEN | MVP-22 |
| 15 | Pilot school | Client introduces at least one candidate school | OPEN | — |
| 16 | Pilot timing | Term 1 2027, from February | PROPOSED | D-11 |
| 17 | WhatsApp sender | Client-owned Meta Business account and dedicated phone number; **verification not started** | PROPOSED — urgent | C-04 |
| 18 | Success metric | e.g. % of trips where every guardian got a "boarded" message | OPEN | — |
| 19 | Wireframes | The 11 screens are the design baseline | DECIDED (14 Oct) | D-23 |
| 20 | Child ID cards | A code the crew scans, later; the data model prepares now. Technology (QR or NFC) and who pays for cards are open | DECIDED (direction) | D-24 |
| 21 | Consent wording | The text guardians agree to on their link. Draft `2026-10-draft` is in the app; the client approves it (or their lawyer edits it) | OPEN — needed before the pilot | D-27 |
| 22 | Privacy contact | Who guardians contact about their data; it goes into the consent wording | OPEN — needed before the pilot | D-27 |

## How to use this page

1. Anne takes `PROPOSED` and `OPEN` rows to the client.
2. Once answered, set `DECIDED`, add the decision to `DECISIONS.md` with the next ID, and reference it here.
3. Most urgent now: **17** (Meta verification blocks Sprint 5), **21 and 22** (needed before any guardian consents
   for real), **7** (which messages to build first), **6** and **15**.
