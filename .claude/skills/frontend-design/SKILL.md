---
name: frontend-design
description: Build production-grade UI components and pages using shadcn/ui primitives, Tailwind, dark mode, and i18n. Use whenever creating or modifying user-facing screens or components.
allowed-tools: Read, Write, Edit, Bash, Grep
---

# /frontend-design

You build polished, accessible, internationalized UI for ServiceCat (Next.js 14 App Router, `servicecat-fe/`). The aesthetic is clean infrastructure-tooling — Linear meets Backstage; functional, not decorative. **Read the existing pages first** (`app/services/page.tsx`, `app/services/[id]/page.tsx`, `app/findings/page.tsx`) and reuse their patterns — don't invent new abstractions.

## What actually exists (use these; don't reinvent)

- **Primitives**: hand-written shadcn (v3) in `components/ui/*` — `Button`, `Card`, `Input`, `Label`, `Table`, `Dialog`, `Badge`, `Select`, `Sonner`. Never raw `<button>/<input>`. (`Table` already wraps in `overflow-auto`, so it scrolls on mobile.)
- **Shared components**: `<AppHeader />` (nav + theme + logout), `<SeverityBadge severity={...} />`, `<FindingsTable />`.
- **Data access**: `apiFetch<T>` from `@/lib/api/client`. Responses are **enveloped** — unwrap `.data` (see envelope rules below).
- **Types**: generated in `@/lib/api/schema` → `components["schemas"]["ServiceResponse"]`. Regenerate after a backend shape change with `pnpm openapi:gen` (API must be running on :8000).
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
import { useAuthStore } from "@/lib/store/auth";

type ServiceList = components["schemas"]["ServiceListResponse"];

export default function ServicesPage() {
  const { ready } = useRequireAuth();
  const t = useTranslations("services");
  const tc = useTranslations("common");
  const workspaceId = useAuthStore((s) => s.workspaceId);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["services", workspaceId],
    queryFn: () => apiFetch<ServiceList>("/api/v1/services"),
    enabled: ready && Boolean(workspaceId),
  });

  if (!ready) return null;
  const services = data?.data ?? [];

  return (
    <div className="min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-5xl px-6 py-8">
        {/* header row: title + primary action */}
        {isLoading ? <p className="text-muted-foreground">{tc("loading")}</p> : null}
        {isError ? <p className="text-destructive">{t("loadError")}</p> : null}
        {!isLoading && services.length === 0 ? (
          <div className="rounded-lg border border-dashed p-10 text-center text-muted-foreground">
            {t("empty")}
          </div>
        ) : null}
        {/* table when services.length > 0 */}
      </main>
    </div>
  );
}
```

`loading.tsx` is a centered `Loader2` spinner; `error.tsx` is a `"use client"` boundary with a retry `Button`. Copy the ones in `app/services/`.

## The response envelope (critical)

The API wraps responses. Unwrap inside the query/mutation fn so component logic stays clean:

- **Single resource** → `apiFetch<Data<Service>>(...).then((r) => r.data)` (`Data<T>` from `@/lib/api/client`).
- **Paginated list** → `apiFetch<ServiceListResponse>(...)` then read `.data` / `.meta`.
- **Simple list** → `apiFetch<Data<Dependency[]>>(...).then((r) => r.data)`.
- **Login/refresh tokens** are flat (no envelope).

## State management

| Need | Tool |
|------|------|
| Server data | `useQuery` / `useMutation` (TanStack Query); `invalidateQueries` after mutations |
| Forms | React Hook Form + Zod (`zodResolver`). For numeric inputs use `register("tier", { valueAsNumber: true })`, not `z.coerce` |
| Global client state | Zustand (`@/lib/store/auth`) |
| Toasts | `toast` from `sonner` |
| URL state (filters) | `useState` locally, or `useSearchParams` if it must be shareable |

## Severity & badges

Reuse the existing component — don't re-derive a color map:
```tsx
import { SeverityBadge } from "@/components/severity-badge";
<SeverityBadge severity={finding.severity} />   // critical/high→destructive, medium→secondary, low→outline
```
Badges are `whitespace-nowrap` (won't wrap). Use `<Badge>` for any status/tier, never raw colored text.

## Dialogs

`Dialog` + `DialogContent` must contain **both** `DialogTitle` and `DialogDescription` (Radix a11y — a missing description warns in console). See `components/create-service-dialog.tsx`.

## i18n

```tsx
const t = useTranslations("services");
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
- Re-derive a severity color map — reuse `<SeverityBadge>`.
- Reference components that don't exist (no `PageLayout`/`EmptyState`/`@tanstack/react-table` here) — inline the states like the existing pages.
- Forget the route trio (`page`/`loading`/`error`), the `useRequireAuth` guard, or unwrapping the `{data}` envelope.
- Run `pnpm build` while `next dev` is running on the same directory.
