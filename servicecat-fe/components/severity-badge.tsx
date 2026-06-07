"use client";

import { useTranslations } from "next-intl";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type Variant = "default" | "secondary" | "destructive" | "outline";

/**
 * Four visually distinct steps using only semantic tokens (dark mode free):
 * critical = solid destructive, high = soft destructive tint, medium =
 * secondary, low = outline. Labels carry the meaning too — color is never
 * the only signal.
 */
const SEVERITY_STYLES: Record<string, { variant: Variant; className?: string }> = {
  critical: { variant: "destructive" },
  high: {
    variant: "outline",
    className: "border-transparent bg-destructive/15 text-destructive",
  },
  medium: { variant: "secondary" },
  low: { variant: "outline" },
};

const KNOWN_SEVERITIES = new Set(Object.keys(SEVERITY_STYLES));

export function SeverityBadge({ severity }: { severity: string }) {
  const t = useTranslations("findings");
  const label = KNOWN_SEVERITIES.has(severity) ? t(`severity.${severity}`) : severity;
  const style = SEVERITY_STYLES[severity] ?? { variant: "outline" as const };
  return (
    <Badge variant={style.variant} className={cn("capitalize", style.className)}>
      {label}
    </Badge>
  );
}
