# User Interview Guide (C-03)

> For the Sprint 0 carry-over C-03: at least 2 conversations before Term 3 closes.
> Each conversation takes about 20 minutes. Record findings in [`ux-research.md`](ux-research.md) using the
> note template at the end. Owner: Anne.

## Who to talk to

| Role | Why | Priority |
|---|---|---|
| School transport coordinator (or bursar / deputy who runs transport) | Buyer and daily user; validates the admin workflow and who pays | 1 |
| Parent whose child uses the school bus | Validates the core promise and the WhatsApp messages | 1 |
| School bus driver | Validates the driver workflow, phone and data reality | 2 |

## Before you start (say this)

> "We're designing a service that sends parents WhatsApp updates about their child's school bus. We're not
> selling anything today, just learning how things work now. There are no right answers. I'll take notes but
> won't record names of children. Is that OK?"

Rules for the interviewer:

- Ask about **what they do now**, not what they'd like in theory.
- Ask "Tell me about the last time…" instead of "Would you…".
- Don't show or describe Tafi's features until the last question.
- Never write down children's names or parents' phone numbers.

## School transport coordinator

1. Walk me through a normal morning for the buses, from the first pickup to arrival at school.
2. How do you know which children are on which bus each day? Where is that written down?
3. Tell me about the last time a parent called asking where the bus was. How often does that happen?
4. Tell me about the last time something went wrong (late bus, child missed, breakdown). How did parents find out?
5. How do you communicate with parents today (WhatsApp groups, SMS, calls)? What works, and what doesn't?
6. How are transport fees charged: per term or per month? How do you track who has paid?
7. Who would decide whether the school pays for a service like this? What would they need to see?
8. **(Last)** If parents got a WhatsApp message when their child boarded and when the bus was 5 minutes away,
   what would change for you? What would worry you about it?

## Parent

1. Tell me about this morning: how did your child get to the bus, and when did you know they arrived at school?
2. Tell me about the last time you didn't know where the bus was. What did you do?
3. Who do you call or message when you're worried: the school, the driver, other parents?
4. Which apps do you use most on your phone? Do you read WhatsApp messages from businesses?
5. **(Last)** Imagine getting these WhatsApp messages: "Your child boarded the bus at 6:42", "The bus is 5
   minutes away", "Your child was dropped off at 16:10". Which matters most to you? Which would you ignore?
   How early is "5 minutes away" useful?
6. Would you be comfortable with the school sharing your number for these messages? What would you want to know first?

## Driver

1. Walk me through your morning route, from starting the bus to the last drop-off.
2. How do you know which children to pick up and where? What happens if a child isn't at the stop?
3. Do parents call you while you're driving? How often?
4. What phone do you use (Android or iPhone)? Who pays for your data bundles? Does your phone stay charged all day?
5. **(Last)** If you had to tap a button on your phone when each child gets on and off, when could you do it
   safely? What would make that hard?

## Note template (copy into `ux-research.md`)

```text
### Interview — <role>, <school type/area>, <date>
- Interviewer: Anne
- Current process: …
- Biggest pain (their words): …
- Tools/channels today: …
- Reaction to the WhatsApp messages: …
- Surprises / things we assumed wrong: …
- Affects: <owner-decisions row #s or MVP items, e.g. row 9 "approaching" threshold, MVP-10>
```

## What these answers decide

| Question area | Feeds |
|---|---|
| Which messages parents value; how early "approaching" helps | owner-decisions rows 7 and 9; T1-03 templates |
| Driver phone, data, when tapping is safe | owner-decisions row 8; T1-02 driver wireframes; T1-11 spike |
| Per term vs per month fees; how payment is tracked | owner-decisions row 10; MVP-16 |
| Who decides to buy; what they need to see | owner-decisions row 11; pilot pitch |
| Parent comfort with number sharing | owner-decisions row 13; consent flow (MVP-05) |
| Coordinator's morning routine | T1-01 school admin wireframes |
