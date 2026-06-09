"use client";

import { useTranslations } from "next-intl";

import { Badge } from "@/components/ui/badge";

type Variant = "default" | "secondary" | "outline" | "brand";

/** Tier 1 is the most critical — brand emphasis, fading to a quiet outline. */
const TIER_VARIANT: Record<number, Variant> = {
  1: "brand",
  2: "secondary",
  3: "outline",
};

export function TierBadge({ tier }: { tier: number }) {
  const t = useTranslations("services");
  return (
    <Badge variant={TIER_VARIANT[tier] ?? "outline"} className="font-mono text-[11px]">
      {t("tierLabel", { tier })}
    </Badge>
  );
}
