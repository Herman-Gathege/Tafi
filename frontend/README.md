# Tafi web app

React 19 + TypeScript + Vite, Tailwind v4, TanStack Query and React Router. Design tokens are carried over from
the client's prototype (see `src/styles.css`).

The app has two sides. The **public side** is what anyone can open while Tafi is being built. The **protected
side** is the school portal, behind a session check.

| Route | Side | What it is |
|---|---|---|
| `/` | Public | Landing page |
| `/wireframes` | Public | The MVP 1 wireframes, with a jump-to-screen list |
| `/signin` | Public | Sign in |
| `/accept-invite` | Public | Set up the account an invitation was for (needs `?token=`) |
| `/forgot-password` | Public | Ask for a reset link |
| `/reset-password` | Public | Choose a new password (needs `?token=`) |
| `/app` | Protected | School portal — today's placeholder |
| `/app/admin` | Protected, Tafi staff | Onboard schools and invite their first admin |

The session is an httpOnly cookie set by the API; the browser cannot read it, so `src/lib/session.ts` asks
`GET /api/v1/auth/me` and caches the answer with TanStack Query. `src/components/require-auth.tsx` holds both
guards: `RequireAuth` for anyone signed in, `RequirePlatformAdmin` for Tafi staff.

Two things are deliberately not real yet, and both are called out in the UI: nothing sends email or WhatsApp
(Sprint 5), so in `local` the API returns reset and invite links in the response and the pages show them; and
there is no refresh token, so a session simply lasts 12 hours.

## The wireframes

Anne's Sprint 1 deck lives at `public/wireframes/tafi-mvp1-wireframes.html` — one self-contained file holding
eleven screens, stacked vertically. It is served at `/wireframes/tafi-mvp1-wireframes.html` and can also be
opened straight from disk in a browser. The gallery page finds each screen in the deck by its heading and
scrolls to it, so the deck's headings are the contract: rename one in the export and update the same string in
`src/routes/wireframes.tsx`.

See [`../docs/ux/wireframes.md`](../docs/ux/wireframes.md) for what each screen shows.

## Run it

The easiest way is the whole stack from the repository root: `make up` (API on
<http://localhost:8000>, web on <http://localhost:5173>).

**Node 22.12 or newer is required** (Vite 8 does not run on Node 21). If you use nvm,
`nvm use` picks up `.nvmrc`. Docker and CI already use Node 22.

On its own:

```sh
npm install
npm run dev
```

The API base URL comes from `VITE_API_BASE_URL` and falls back to `http://localhost:8000`.

## Checks

```sh
npm run lint
npm run typecheck
npm run build
```

## Layout

- `src/routes/` — one file per route.
- `src/components/ui/` — small accessible primitives. Add more as the wireframes land.
- `src/lib/api.ts` — the typed client for the FastAPI backend. Keep it the only place that talks HTTP.
