"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertCircle, CheckCircle2, Circle } from "lucide-react";
import { useTranslations } from "next-intl";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch, type Data } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { cn } from "@/lib/utils";

type Insights = components["schemas"]["EventInsightsResponse"];
type Readiness = components["schemas"]["EventReadinessResponse"];

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-xl border bg-muted/30 px-4 py-3">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 font-display text-2xl font-semibold tabular-nums">{value}</p>
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}

export function EventInsights({ eventId, enabled }: { eventId: string; enabled: boolean }) {
  const t = useTranslations("detail");

  const insights = useQuery({
    queryKey: ["insights", eventId],
    queryFn: () =>
      apiFetch<Data<Insights>>(`/api/v1/events/${eventId}/insights`).then((res) => res.data),
    enabled,
  });
  const readiness = useQuery({
    queryKey: ["readiness", eventId],
    queryFn: () =>
      apiFetch<Data<Readiness>>(`/api/v1/events/${eventId}/readiness`).then((res) => res.data),
    enabled,
  });

  const data = insights.data;
  const checks = readiness.data;

  return (
    <div className="grid gap-4 lg:grid-cols-5">
      <Card className="animate-fade-up lg:col-span-3">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{t("insights.title")}</CardTitle>
        </CardHeader>
        <CardContent>
          {data ? (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Stat
                label={t("insights.responseRate")}
                value={`${Math.round(data.response_rate * 100)}%`}
              />
              <Stat
                label={t("insights.attending")}
                value={String(data.attending)}
                hint={
                  data.capacity === null
                    ? t("insights.uncapped")
                    : t("insights.ofCapacity", { capacity: data.capacity })
                }
              />
              <Stat label={t("insights.checkedIn")} value={String(data.checked_in)} />
              <Stat label={t("insights.plusOnes")} value={String(data.plus_ones)} />
            </div>
          ) : (
            <div className="h-20 animate-pulse rounded-xl bg-muted/40" />
          )}
        </CardContent>
      </Card>

      <Card className="animate-fade-up [animation-delay:60ms] lg:col-span-2">
        <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
          <CardTitle className="text-base">{t("readiness.title")}</CardTitle>
          {checks ? (
            <Badge variant={checks.ready ? "brand" : "warning"}>
              {checks.ready ? t("readiness.ready") : t("readiness.notReady")}
            </Badge>
          ) : null}
        </CardHeader>
        <CardContent>
          {checks ? (
            <>
              <p className="mb-3 text-sm text-muted-foreground">
                {t("readiness.score", { passed: checks.passed, total: checks.total })}
              </p>
              <ul className="space-y-1.5">
                {checks.checks.map((check) => (
                  <li key={check.key} className="flex items-center gap-2.5 text-sm">
                    {check.passed ? (
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-success" aria-hidden="true" />
                    ) : check.severity === "high" ? (
                      <AlertCircle className="h-4 w-4 shrink-0 text-warning" aria-hidden="true" />
                    ) : (
                      <Circle className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                    )}
                    <span className={cn(check.passed ? "" : "text-muted-foreground")}>
                      {t(`readiness.checks.${check.key}`)}
                    </span>
                    {!check.passed && check.severity !== "low" ? (
                      <span className="ml-auto text-xs text-muted-foreground">
                        {t(`readiness.severity.${check.severity}`)}
                      </span>
                    ) : null}
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <div className="h-32 animate-pulse rounded-xl bg-muted/40" />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
