# Homework — Sprint 1

> Sprint 1 closed Thu 9 Oct 2026 with four of its six Definition of Done items met. Everything still open is
> below. Source: [`../docs/sprints/sprint-1.md`](../docs/sprints/sprint-1.md#review--close-out).

## Anne

### H1-1 — WhatsApp template copy for the client to approve (T1-03)

- **Left over:** the wireframes show the message designs, but the actual wording of each template — trip started,
  boarded, bus approaching, dropped off, absent, and the failure case — is not drafted or approved.
- **Why it matters:** Meta must approve the templates before a single parent message can be sent, and approval
  takes time. Sprint 3 submits them, so the copy is needed by the start of Sprint 3.
- **Next action:** write the six templates as plain copy, take them to the client with the wireframe screen
  "Option A · Parent WhatsApp messages", and record the approved wording in the repository.
- **Tracked:** T1-03, MVP-12, MVP-13.

### H1-2 — WhatsApp Cloud API spike (T1-15)

- **Left over:** template categories (utility vs marketing), approval lead time, and the cost of a utility
  message per conversation.
- **Why it matters:** cost scales with children × messages per day, so it decides whether SMS fallback is
  affordable and what the client pays per child.
- **Next action:** answer it the same way as T1-11 to T1-14 and append the section to
  [`../docs/architecture/spikes/sprint-1-spikes.md`](../docs/architecture/spikes/sprint-1-spikes.md).
- **Tracked:** T1-15.

### H1-3 — Client review of the MVP 1 scope and the `PROPOSED` decisions (T1-05, carry-over C-01)

- **Left over:** the client has not acknowledged the rebuild plan or reviewed the `PROPOSED` rows in
  [`../docs/product/owner-decisions.md`](../docs/product/owner-decisions.md).
- **Why it matters:** the MVP 1 scope rests on those rows. Rows 6, 8, 9, 10 and 11 change what Sprint 3 builds.
- **Next action:** walk the client through the scope and the rows; record each answer in `DECISIONS.md` with the
  next ID and set the row to `DECIDED`.
- **Tracked:** T1-05, C-01.

### H1-4 — Retire the stale hypothesis labels (T1-04)

- **Left over:** `ASSUMPTION` markers remain in the product and UX docs where the client has since decided
  (a single school pilot, WhatsApp-only parents, manual payments, and so on).
- **Why it matters:** leftover assumptions hide which parts of the plan are still guesses.
- **Next action:** read [`../docs/DECISIONS.md`](../docs/DECISIONS.md) and clear every label it already answers.
- **Tracked:** T1-04.

### H1-5 — User conversations (carry-over C-03)

- **Left over:** no conversations with a school transport coordinator, a driver or a parent.
- **Why it matters:** the wireframes and the "bus approaching" threshold are still designed from desk research.
  The guide is written and the school term is the deadline.
- **Next action:** run at least two conversations using
  [`../docs/ux/interview-guide.md`](../docs/ux/interview-guide.md) and record them in `docs/ux/ux-research.md`.
- **Tracked:** C-03, owner-decision rows 8, 9, 10, 13.

## Herman

### H1-6 — Open the pull request for the Sprint 1 foundation

- **Left over:** `feature/sprint-1-foundation` is pushed with green CI, but no pull request is open, so nothing
  has been reviewed or merged. PR #4 (the Sprint 0 close-out) is also still open.
- **Why it matters:** unreviewed work is invisible work, and this branch contains the wireframes, the review
  gallery and the public/protected split.
- **Next action:** open the pull request against `main`, ask Anne to review, and merge PR #4 first if this branch
  is to sit on top of it cleanly.
- **Tracked:** T1-10, [`../docs/CONTRIBUTING.md`](../docs/CONTRIBUTING.md).

### H1-7 — Make `annewaithaka/Tafi` private (carry-over C-02)

- **Left over:** the repository is still publicly readable; the keys in the old `.env` are only neutralised once
  the client deletes the Lovable project.
- **Why it matters:** it is the client's code and the last open piece of Sprint 0's security hygiene.
- **Next action:** Anne changes the repository visibility (it needs repo admin), and Herman confirms his own copy
  stays private.
- **Tracked:** C-02, D-14, D-15.

## Client

### H1-8 — Long-lead actions (carry-over C-04)

- **Left over:** Meta Business verification and a dedicated WhatsApp number; an introduction to at least one pilot
  school; disconnecting GitHub from the Lovable project and deleting it.
- **Why it matters:** verification gates every parent message, and no pilot school means nothing to validate
  against. Starting late pushes the pilot out of Term 1.
- **Next action:** Anne chases all three in one conversation with the client.
- **Tracked:** C-04.

### H1-9 — Two scope questions the wireframes raised

- **Left over:** the school portal shows **Trips** and **Settings** sections that MVP 1 does not list, and the
  parent experience is drawn twice — **Option A** (WhatsApp messages plus a registration page) and **Option B**
  (a parent web dashboard). D-12 says WhatsApp only, so Option B is unconfirmed.
- **Why it matters:** deciding late means building a screen twice, or building one nobody asked for.
- **Next action:** put both questions to the client alongside the scope review (H1-3), and record the answers in
  `DECISIONS.md`. If Trips and Settings are wanted, add them to the MVP 1 backlog.
- **Tracked:** owner-decision row 9, MVP-14, MVP-15, MVP-16.
