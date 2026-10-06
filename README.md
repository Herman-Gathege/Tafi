# Tafi

A parent safety service for transport in Kenya. Parents get WhatsApp updates when their child boards, is dropped
off, or the bus is approaching. Schools are the first customers; other transport providers follow.

## Status

**Sprint 1 — UX + Foundation (19–30 Oct 2026).** Sprint 0 closed on 6 Oct 2026.
See [`docs/STATUS.md`](docs/STATUS.md), [`docs/sprints/sprint-0.md`](docs/sprints/sprint-0.md) and
[`docs/sprints/sprint-1.md`](docs/sprints/sprint-1.md).

## Repository contents

- `docs/` — planning, decisions, research and sprints. Start at [`docs/README.md`](docs/README.md).
- `src/`, `supabase/`, `tafi-landing.html` — the client-supplied **prototype** (built with Lovable). Reference only;
  it will be replaced by the rebuild. Do not extend it.

## Planned stack

React · FastAPI · PostgreSQL · Redis · background worker · Docker Compose · DigitalOcean.
Details: [`docs/architecture/architecture-decision.md`](docs/architecture/architecture-decision.md).

## Contributing

See [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) and [`AGENTS.md`](AGENTS.md).
