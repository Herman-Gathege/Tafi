# Tafi Product Brief

> Direction **confirmed by the client** on 5 Oct 2026 (D-04 to D-07, D-12). Items marked PROPOSED or ASSUMPTION
> still need confirmation.

## Product

Tafi is a **parent safety service for transport**. Parents receive WhatsApp updates about their child's trip:

- "Wanjiru boarded bus KCA 123X at 6:42"
- "The bus is 5 minutes away"
- "Wanjiru was dropped off at 16:10"

Transport providers pay for Tafi so they can give parents this peace of mind. (DECIDED)

## Who pays, who benefits

| Party | Role | Pays |
|---|---|---|
| School (MVP 1) | Runs buses; manages students, routes and drivers in Tafi | Pays Tafi (D-06) |
| Independent transport provider (later) | Same, outside a school | Pays Tafi (later, D-05) |
| Parent / guardian | Receives WhatsApp updates; no app | Pays the school for transport (D-06) |
| Driver | Records the trip and each child's boarding on a phone | — |
| Tafi platform admin (client) | Onboards providers, sets pricing, bills providers | — |

## Problem (ASSUMPTION — validate in user conversations)

Parents don't know whether the bus is coming, whether their child boarded, or when they were dropped off, so they
call the school and the driver. Schools coordinate transport through WhatsApp groups, calls and paper.

## MVP 1 — school transport

Core loop (PROPOSED detail, see `owner-decisions.md`):

1. Tafi platform admin onboards a school and invites its first admin.
2. School admin adds students, guardians, routes, stops, vehicles and drivers (manually or by CSV).
3. Guardians are registered with WhatsApp numbers and their consent is recorded.
4. Driver opens today's trip on a phone, starts it, and marks each child boarded or dropped off. Location is shared
   during the trip.
5. Tafi sends guardians WhatsApp updates: trip started, boarded, bus approaching, dropped off.
6. School tracks transport fees per term; Tafi bills the school using the client's configured pricing.

## Later (not MVP 1)

- Independent transport providers and non-school transport.
- M-Pesa payment automation.
- QR-scan check-in, SMS fallback, reporting.

## Out of scope for MVP 1

- Parent mobile app.
- Dedicated GPS hardware.
- M-Pesa automation.
- Non-school providers.

## Unknowns

- How Tafi charges schools (unit, frequency, free pilot period).
- Driver device reality: smartphone, data bundles, who pays for data.
- Whether schools bill parents per term or per month.
- Guardian consent process and data-protection obligations.
