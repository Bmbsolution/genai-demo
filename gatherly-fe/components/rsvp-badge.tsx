"use client";

import { useTranslations } from "next-intl";

import { cn } from "@/lib/utils";

/**
 * RSVP status as a dot + tinted pill + label (never color alone):
 * yes = success, maybe = warning, no = destructive, pending = quiet outline.
 */
const STYLES: Record<string, string> = {
  yes: "border-success/30 bg-success/15 text-success",
  maybe: "border-warning/30 bg-warning/15 text-warning",
  no: "border-destructive/30 bg-destructive/10 text-destructive",
  pending: "border-border bg-transparent text-muted-foreground",
};

const DOT: Record<string, string> = {
  yes: "bg-success",
  maybe: "bg-warning",
  no: "bg-destructive",
  pending: "bg-muted-foreground",
};

const KNOWN = new Set(Object.keys(STYLES));

export function RsvpBadge({ status }: { status: string }) {
  const t = useTranslations("rsvp");
  const label = KNOWN.has(status) ? t(`status.${status}`) : status;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-semibold capitalize",
        STYLES[status] ?? STYLES.pending,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", DOT[status] ?? DOT.pending)} />
      {label}
    </span>
  );
}
