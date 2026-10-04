# Contributing & Review Process

> The development process for Tafi. Keep it short and follow it. See [`README.md`](README.md)
> for the documentation map and [`../AGENTS.md`](../AGENTS.md) for agent instructions.

## Branching

- Never commit directly to `main`.
- Branch names: `feature/<name>`, `fix/<name>`, `research/<name>`, `codex/<name>`.
- Every meaningful change is independently reviewable.

## Pull requests (required)

- All documentation, process, and code changes go through a pull request targeting `main`.
- The PR description must be written for **both the owner and the co-dev**.
- The author does **not** merge their own PR.

## Co-dev alignment

- This project uses an explicit **alignment checkpoint**: the co-dev and owner review the
  PR and its linked documentation before implementation continues.
- **Lack of comments is not automatic approval.**

## Sprint discipline

Every sprint has: **Goal · Tasks · Deliverables · Definition of Done · Review · Next sprint.**

## Documentation

- Keep documentation short, current, and decision-oriented (see `docs/README.md`).
- Label claims **FACT / OBSERVATION / ASSUMPTION / UNKNOWN**.
- Unconfirmed direction lives in `docs/product/owner-decisions.md`; confirmed decisions in `docs/DECISIONS.md`.
