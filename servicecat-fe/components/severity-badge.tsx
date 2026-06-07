"use client";

import { useTranslations } from "next-intl";

import { Badge } from "@/components/ui/badge";

type Variant = "default" | "secondary" | "destructive" | "outline";

const SEVERITY_VARIANT: Record<string, Variant> = {
  critical: "destructive",
  high: "destructive",
  medium: "secondary",
  low: "outline",
};

const KNOWN_SEVERITIES = new Set(["critical", "high", "medium", "low"]);

export function SeverityBadge({ severity }: { severity: string }) {
  const t = useTranslations("findings");
  const label = KNOWN_SEVERITIES.has(severity) ? t(`severity.${severity}`) : severity;
  return (
    <Badge variant={SEVERITY_VARIANT[severity] ?? "outline"} className="capitalize">
      {label}
    </Badge>
  );
}
