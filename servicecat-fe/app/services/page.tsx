"use client";

import { useQuery } from "@tanstack/react-query";
import { Boxes } from "lucide-react";
import { useTranslations } from "next-intl";
import Link from "next/link";

import { AppHeader } from "@/components/app-header";
import { CreateServiceDialog } from "@/components/create-service-dialog";
import { TierBadge } from "@/components/tier-badge";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { useAuthStore } from "@/lib/store/auth";

type ServiceList = components["schemas"]["ServiceListResponse"];

export default function ServicesPage() {
  const { ready } = useRequireAuth();
  const t = useTranslations("services");
  const tc = useTranslations("common");
  const workspaceId = useAuthStore((state) => state.workspaceId);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["services", workspaceId],
    queryFn: () => apiFetch<ServiceList>("/api/v1/services"),
    enabled: ready && Boolean(workspaceId),
  });

  if (!ready) return null;

  const services = data?.data ?? [];

  return (
    <div className="min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-5xl px-6 py-8">
        <div className="mb-6 flex items-end justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h1 className="font-display text-3xl font-semibold tracking-tight">{t("title")}</h1>
              {services.length > 0 ? (
                <Badge variant="secondary" className="font-mono">
                  {services.length}
                </Badge>
              ) : null}
            </div>
            <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
          </div>
          <CreateServiceDialog />
        </div>

        {isLoading ? <p className="text-muted-foreground">{tc("loading")}</p> : null}
        {isError ? <p className="text-destructive">{t("loadError")}</p> : null}

        {!isLoading && !isError && services.length === 0 ? (
          <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed bg-card/40 p-12 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted text-muted-foreground">
              <Boxes className="h-6 w-6" aria-hidden="true" />
            </span>
            <p className="text-sm text-muted-foreground">{t("empty")}</p>
            <CreateServiceDialog />
          </div>
        ) : null}

        {services.length > 0 ? (
          <div className="animate-fade-up overflow-hidden rounded-xl border bg-card shadow-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("columns.name")}</TableHead>
                  <TableHead>{t("columns.tier")}</TableHead>
                  <TableHead>{t("columns.repo")}</TableHead>
                  <TableHead>{t("columns.description")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {services.map((service, i) => (
                  <TableRow
                    key={service.id}
                    className="animate-fade-up"
                    style={{ animationDelay: `${i * 45}ms` }}
                  >
                    <TableCell className="font-medium">
                      <Link
                        href={`/services/${service.id}`}
                        className="group inline-flex items-center gap-2.5 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                      >
                        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-border bg-muted font-mono text-xs font-semibold uppercase text-muted-foreground transition-colors group-hover:border-brand/40 group-hover:text-brand">
                          {service.name.slice(0, 2)}
                        </span>
                        <span className="group-hover:text-brand group-hover:underline">
                          {service.name}
                        </span>
                      </Link>
                    </TableCell>
                    <TableCell>
                      <TierBadge tier={service.tier} />
                    </TableCell>
                    <TableCell
                      className="max-w-xs truncate font-mono text-xs text-muted-foreground"
                      title={service.repo_url}
                    >
                      {service.repo_url}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {service.description ?? "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        ) : null}
      </main>
    </div>
  );
}
