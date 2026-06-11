# Gatherly — frontend

Next.js 14 + Tailwind + shadcn/ui, on the "Instrument" design system shared
with ServiceCat. The demo app for the talk: plan events, invite guests,
collect RSVPs.

## Run

```bash
pnpm install
pnpm dev -p 3002        # API expected at http://127.0.0.1:8002 (.env.local)
```

Screens: `/login`, `/events`, `/events/[id]` (guest list + RSVP summary),
`/rsvp/[token]` (public guest RSVP — no login).

## Checks

```bash
pnpm test         # vitest
pnpm lint         # eslint
pnpm exec tsc --noEmit
pnpm build
```
