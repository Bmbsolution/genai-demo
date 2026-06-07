"use client";

import { useTranslations } from "next-intl";

import { Badge } from "@/components/ui/badge";

type Variant = "default" | "secondary" | "outline";

/** Tier 1 is the most critical — emphasis decreases with the tier number. */
const TIER_VARIANT: Record<number, Variant> = {
  1: "default",
  2: "secondary",
  3: "outline",
};

export function TierBadge({ tier }: { tier: number }) {
  const t = useTranslations("services");
  return <Badge variant={TIER_VARIANT[tier] ?? "outline"}>{t("tierLabel", { tier })}</Badge>;
}
