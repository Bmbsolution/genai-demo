"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Sparkles } from "lucide-react";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch, type Data } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type Overview = components["schemas"]["BillingOverviewResponse"];
type Checkout = components["schemas"]["CheckoutResponse"];

export function BillingCard({ enabled }: { enabled: boolean }) {
  const t = useTranslations("billing");
  const queryClient = useQueryClient();

  const billing = useQuery({
    queryKey: ["billing"],
    queryFn: () => apiFetch<Data<Overview>>("/api/v1/billing").then((r) => r.data),
    enabled,
  });

  const upgrade = useMutation({
    mutationFn: async () => {
      const checkout = await apiFetch<Data<Checkout>>("/api/v1/billing/checkout", {
        method: "POST",
      });
      // Real Stripe returns a hosted URL to redirect to; the mock provider has
      // us complete the upgrade in-app.
      if (checkout.data.url) {
        window.location.href = checkout.data.url;
        return;
      }
      await apiFetch("/api/v1/billing/upgrade", { method: "POST" });
    },
    onSuccess: async () => {
      toast.success(t("upgraded"));
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["billing"] }),
        queryClient.invalidateQueries({ queryKey: ["me"] }),
      ]);
    },
    onError: () => toast.error(t("upgradeFailed")),
  });

  const data = billing.data;
  const isPro = data?.plan === "pro";

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">{t("title")}</CardTitle>
        {data ? (
          <Badge variant={isPro ? "brand" : "secondary"}>{isPro ? t("pro") : t("free")}</Badge>
        ) : null}
      </CardHeader>
      <CardContent className="space-y-5">
        {data ? (
          <>
            <p className="text-sm text-muted-foreground">
              {isPro
                ? t("proBlurb")
                : t("freeBlurb", {
                    events: data.max_active_events ?? 0,
                    guests: data.max_guests_per_event ?? 0,
                  })}
            </p>

            {isPro ? (
              <p className="inline-flex items-center gap-2 text-sm font-medium text-brand">
                <Sparkles className="h-4 w-4" aria-hidden="true" />
                {t("onPro")}
              </p>
            ) : (
              <>
                {data.max_active_events !== null ? (
                  <p className="text-sm tabular-nums text-muted-foreground">
                    {t("usage", { active: data.active_events, limit: data.max_active_events })}
                  </p>
                ) : null}
                <div className="rounded-xl border bg-muted/30 p-4">
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    {t("proFeatures")}
                  </p>
                  <ul className="space-y-1.5">
                    {["events", "guests", ...data.pro_features].map((feature) => (
                      <li key={feature} className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 shrink-0 text-success" aria-hidden="true" />
                        {t(`feature.${feature}`)}
                      </li>
                    ))}
                  </ul>
                </div>
                <Button disabled={upgrade.isPending} onClick={() => upgrade.mutate()}>
                  <Sparkles className="mr-2 h-4 w-4" />
                  {upgrade.isPending
                    ? t("upgrading")
                    : t("upgrade", { price: data.price_display })}
                </Button>
              </>
            )}
          </>
        ) : (
          <div className="h-28 animate-pulse rounded-xl bg-muted/40" />
        )}
      </CardContent>
    </Card>
  );
}
