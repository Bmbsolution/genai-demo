---
name: frontend-design
description: Build production-grade UI components and pages using shadcn/ui primitives, Tailwind, dark mode, and i18n. Use whenever creating or modifying user-facing screens or components.
allowed-tools: Read, Write, Edit, Bash, Grep
---

# /frontend-design

You build polished, accessible, internationalized UI for Gatherly (Next.js 14 App Router, `gatherly-fe/`). The aesthetic is clean, friendly event-management tooling — functional, not decorative. **Read the existing pages first** (`app/events/page.tsx`, `app/events/[id]/page.tsx`, `app/account/page.tsx`) and reuse their patterns — don't invent new abstractions.

## What actually exists (use these; don't reinvent)

- **Primitives**: hand-written shadcn (v3) in `components/ui/*` — `Button`, `Card`, `Input`, `Label`, `Table`, `Dialog`, `Badge`, `Select`, `Sonner`. Never raw `<button>/<input>`. (`Table` already wraps in `overflow-auto`, so it scrolls on mobile.)
- **Shared components**: `<AppHeader />` (nav + theme + logout), `<StatusBadge status={...} />`, `<GuestListTable />`.
- **Data access**: `apiFetch<T>` from `@/lib/api/client`. Responses are **enveloped** — unwrap `.data` (see envelope rules below).
- **Types**: generated in `@/lib/api/schema` → `components["schemas"]["EventResponse"]`. Regenerate after a backend shape change with `pnpm openapi:gen` (API must be running on :8002).
- **Auth guard**: `useRequireAuth()` from `@/hooks/use-require-auth` on every protected page.
- **i18n**: `next-intl`, keys in `messages/en.json` + `messages/fr.json`.
- **Theme**: `next-themes` (`ThemeToggle` exists). Use semantic tokens; `dark:` only when a token isn't enough.

## Page structure (the real pattern)

Every route folder has **three** files: `page.tsx`, `loading.tsx`, `error.tsx`. Protected pages guard with `useRequireAuth`:

```tsx
"use client";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";

import { AppHeader } from "@/components/app-header";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type EventList = components["schemas"]["EventListResponse"];

export default function EventsPage() {
  const { ready } = useRequireAuth();
  const t = useTranslations("events");
  const tc = useTranslations("common");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["events"],
    queryFn: () => apiFetch<EventList>("/api/v1/events"),
    enabled: ready,
  });

  if (!ready) return null;
  const events = data?.data ?? [];

  return (
    <div className="min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-5xl px-6 py-8">
        {/* header row: title + primary action */}
        {isLoading ? <p className="text-muted-foreground">{tc("loading")}</p> : null}
        {isError ? <p className="text-destructive">{t("loadError")}</p> : null}
        {!isLoading && events.length === 0 ? (
          <div className="rounded-lg border border-dashed p-10 text-center text-muted-foreground">
            {t("empty")}
          </div>
        ) : null}
        {/* table when events.length > 0 */}
      </main>
    </div>
  );
}
```

`loading.tsx` is a centered `Loader2` spinner; `error.tsx` is a `"use client"` boundary with a retry `Button`. Copy the ones in `app/events/`.

## The response envelope (critical)

The API wraps responses. Unwrap inside the query/mutation fn so component logic stays clean:

- **Single resource** → `apiFetch<Data<Event>>(...).then((r) => r.data)` (`Data<T>` from `@/lib/api/client`).
- **Paginated list** → `apiFetch<EventListResponse>(...)` then read `.data` / `.meta`.
- **Simple list** → `apiFetch<Data<Guest[]>>(...).then((r) => r.data)`.
- **Login/refresh tokens** are flat (no envelope).

## State management

| Need | Tool |
|------|------|
| Server data | `useQuery` / `useMutation` (TanStack Query); `invalidateQueries` after mutations |
| Forms | React Hook Form + Zod (`zodResolver`). For numeric inputs use `register("capacity", { valueAsNumber: true })`, not `z.coerce` |
| Global client state | Zustand (`@/lib/store/auth`) |
| Toasts | `toast` from `sonner` |
| URL state (filters) | `useState` locally, or `useSearchParams` if it must be shareable |

## Status & badges

Reuse the existing component — don't re-derive a color map:
```tsx
import { StatusBadge } from "@/components/status-badge";
<StatusBadge status={guest.rsvpStatus} />   // attending→default, declined→destructive, pending→secondary
```
Badges are `whitespace-nowrap` (won't wrap). Use `<Badge>` for any status, never raw colored text.

## Dialogs

`Dialog` + `DialogContent` must contain **both** `DialogTitle` and `DialogDescription` (Radix a11y — a missing description warns in console). See `components/create-event-dialog.tsx`.

## i18n

```tsx
const t = useTranslations("events");
return <h1>{t("title")}</h1>;
```
Add every key to **both** `messages/en.json` AND `messages/fr.json` in the same change. French should be idiomatic, not literal.

## Accessibility & responsive checklist

- [ ] All interactive elements reachable by Tab; **visible** focus rings (`focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2`) — including custom `<Link>`s.
- [ ] Icon-only buttons have `aria-label` (or `sr-only` text); on mobile, collapse non-essential header items rather than overflowing.
- [ ] Color is never the only signal.
- [ ] Works at 390px and 1280px, in light AND dark — verify both (semantic tokens make dark mostly free).
- [ ] Forms: `<Label htmlFor>` associations; modals trap focus and restore it on close.

## Verify before done

- `pnpm lint` and `pnpm exec tsc --noEmit` clean.
- `pnpm test` (Vitest + RTL in `__tests__/`); add tests for new logic/components.
- A production `pnpm build` passes — but **stop `next dev` first** (a concurrent build clobbers the dev `.next` and causes `_next/static` 404s); `rm -rf .next` and restart dev after.

## What you must NOT do

- Use raw HTML form controls, hardcode strings, or hardcode hex colors (use tokens).
- Re-derive an RSVP status color map — reuse `<StatusBadge>`.
- Reference components that don't exist (no `PageLayout`/`EmptyState`/`@tanstack/react-table` here) — inline the states like the existing pages.
- Forget the route trio (`page`/`loading`/`error`), the `useRequireAuth` guard, or unwrapping the `{data}` envelope.
- Run `pnpm build` while `next dev` is running on the same directory.
