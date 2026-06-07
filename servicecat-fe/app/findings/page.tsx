"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { AppHeader } from "@/components/app-header";
import { FindingsTable } from "@/components/findings-table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { useAuthStore } from "@/lib/store/auth";

type FindingList = components["schemas"]["FindingListResponse"];
type ServiceList = components["schemas"]["ServiceListResponse"];

const SEVERITIES = ["critical", "high", "medium", "low"] as const;

export default function FindingsPage() {
  const { ready } = useRequireAuth();
  const t = useTranslations("findings");
  const tc = useTranslations("common");
  const workspaceId = useAuthStore((state) => state.workspaceId);
  const [severity, setSeverity] = useState("all");

  const enabled = ready && Boolean(workspaceId);

  const findings = useQuery({
    queryKey: ["findings", workspaceId, severity],
    queryFn: () =>
      apiFetch<FindingList>(
        `/api/v1/findings${severity === "all" ? "" : `?severity=${severity}`}`,
      ),
    enabled,
  });

  const services = useQuery({
    queryKey: ["services", workspaceId],
    queryFn: () => apiFetch<ServiceList>("/api/v1/services?limit=200"),
    enabled,
  });

  if (!ready) return null;

  const nameById = new Map((services.data?.data ?? []).map((s) => [s.id, s.name]));
  const rows = findings.data?.data ?? [];

  return (
    <div className="min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-5xl px-6 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
            <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
          </div>
          <Select value={severity} onValueChange={setSeverity}>
            <SelectTrigger className="w-44">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("allSeverities")}</SelectItem>
              {SEVERITIES.map((s) => (
                <SelectItem key={s} value={s}>
                  {t(`severity.${s}`)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {findings.isLoading ? <p className="text-muted-foreground">{tc("loading")}</p> : null}
        {findings.isError ? <p className="text-destructive">{t("loadError")}</p> : null}

        {!findings.isLoading && !findings.isError && rows.length === 0 ? (
          <div className="rounded-lg border border-dashed p-10 text-center text-muted-foreground">
            {t("empty")}
          </div>
        ) : null}

        {rows.length > 0 ? <FindingsTable findings={rows} nameById={nameById} /> : null}
      </main>
    </div>
  );
}
