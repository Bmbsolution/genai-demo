"use client";

import { useTranslations } from "next-intl";

import { cn } from "@/lib/utils";

/**
 * Severity as a three-signal token: a colored status dot, a tinted pill, and a
 * label — so it never relies on color alone. Critical is loudest (solid),
 * stepping down to a quiet outline for low.
 */
const SEVERITY_STYLES: Record<string, string> = {
  critical: "border-transparent bg-severity-critical text-white",
  high: "border-severity-high/30 bg-severity-high/10 text-severity-high",
  medium: "border-severity-medium/30 bg-severity-medium/10 text-severity-medium",
  low: "border-border bg-transparent text-muted-foreground",
};

const DOT: Record<string, string> = {
  critical: "bg-white",
  high: "bg-severity-high",
  medium: "bg-severity-medium",
  low: "bg-severity-low",
};

const KNOWN = new Set(Object.keys(SEVERITY_STYLES));

export function SeverityBadge({ severity }: { severity: string }) {
  const t = useTranslations("findings");
  const label = KNOWN.has(severity) ? t(`severity.${severity}`) : severity;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-semibold capitalize",
        SEVERITY_STYLES[severity] ?? SEVERITY_STYLES.low,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", DOT[severity] ?? DOT.low)} />
      {label}
    </span>
  );
}
