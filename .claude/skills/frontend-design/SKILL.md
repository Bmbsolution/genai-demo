---
name: frontend-design
description: Build production-grade UI components and pages using shadcn/ui primitives, Tailwind, dark mode, and i18n. Use whenever creating or modifying user-facing screens or components.
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Grep
context: main
agent: general-purpose
---

# /frontend-design

You build polished, accessible, internationalized UI for ServiceCat. The visual language is a clean, dense, infrastructure-tooling aesthetic: think Linear meets Backstage. Functional, not decorative.

## Design tokens (already set in `servicecat-fe/tailwind.config.ts`)

- **Spacing:** 4-based scale, prefer `gap-2`, `gap-3`, `gap-4` for component spacing
- **Typography:** `font-sans` (Inter), `font-mono` (JetBrains Mono) for code/IDs
- **Color semantics:** `text-foreground`, `text-muted-foreground`, `bg-background`, `bg-card`, `border-border`. Never hardcode hex.
- **Severity colors:** `text-destructive` (CRITICAL), `text-orange-600 dark:text-orange-400` (HIGH), `text-yellow-600 dark:text-yellow-400` (MEDIUM), `text-blue-600 dark:text-blue-400` (LOW)
- **Shadows:** Use sparingly. Cards have `shadow-sm`. Modals have `shadow-lg`.
- **Radius:** `rounded-md` for buttons/inputs, `rounded-lg` for cards.

## Component contract

Every component must:
1. Use shadcn/ui primitives (`Button`, `Card`, `Input`, `Dialog`, `Table`, `Badge`, etc.) — never raw HTML form elements
2. Support dark mode (test both themes)
3. Use i18n via `next-intl` — no hardcoded strings
4. Handle loading, empty, error, and success states
5. Be keyboard-navigable (focus rings visible, escape closes modals, enter submits)
6. Be accessible (semantic HTML, aria-labels for icon buttons, sufficient color contrast)

## State management

| Need | Tool |
|------|------|
| Server data | `useQuery` / `useMutation` from TanStack Query |
| Local form state | React Hook Form + Zod |
| Cross-component state | Zustand |
| URL state (filters, tabs) | `useSearchParams` from Next.js |

## Patterns to follow

### Page structure
```tsx
// app/(dashboard)/services/page.tsx
export default function ServicesPage() {
  return (
    <PageLayout
      title={t("services.title")}
      actions={<Button onClick={openCreateModal}>{t("services.new")}</Button>}
    >
      <ServiceFilters />
      <ServicesTable />
    </PageLayout>
  )
}
```

### Loading / empty / error
```tsx
const { data, isLoading, error } = useServices()

if (isLoading) return <ServicesTableSkeleton />
if (error) return <ErrorState error={error} retry={refetch} />
if (!data?.length) return <EmptyState
  icon={<Inbox />}
  title={t("services.empty.title")}
  description={t("services.empty.description")}
  action={<Button>{t("services.empty.cta")}</Button>}
/>
```

### Forms
```tsx
const schema = z.object({
  name: z.string().min(1).max(100),
  repoUrl: z.string().url(),
  tier: z.enum(["1", "2", "3"]),
})

const form = useForm<z.infer<typeof schema>>({
  resolver: zodResolver(schema),
})
```

### Tables
- Use `@tanstack/react-table` for anything with sorting/filtering
- Compact rows (`py-2 px-3`)
- Right-align numerics
- Use `<Badge>` for status/severity, not raw text

### Severity badges
```tsx
const severityVariants = {
  CRITICAL: "bg-destructive/10 text-destructive border-destructive/30",
  HIGH:     "bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/30",
  MEDIUM:   "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/30",
  LOW:      "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30",
}
```

## i18n

Every user-visible string goes through `useTranslations()`:

```tsx
const t = useTranslations("services")
return <h1>{t("title")}</h1>
```

Add the keys to BOTH `messages/en.json` AND `messages/fr.json` in the same commit. French translations should be polished, not literal — get them right.

## Accessibility checklist

- [ ] All interactive elements reachable with Tab
- [ ] Visible focus rings (Tailwind `focus-visible:ring-2`)
- [ ] Icon-only buttons have `aria-label`
- [ ] Color is never the only signal (icons + colors for severity)
- [ ] Forms have proper `<label>` associations
- [ ] Modals trap focus when open, return focus on close

## What you must NOT do

- Use raw `<button>`, `<input>`, etc. — always shadcn/ui primitives
- Hardcode strings. Always i18n.
- Hardcode hex colors. Always Tailwind tokens.
- Skip dark mode verification.
- Skip the empty/error/loading states. Production UI handles all four.
- Ship without keyboard testing.
