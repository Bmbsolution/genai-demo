"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { AppHeader } from "@/components/app-header";
import { CreateServiceDialog } from "@/components/create-service-dialog";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { useAuthStore } from "@/lib/store/auth";

type ServiceList = components["schemas"]["ServiceListResponse"];

export default function ServicesPage() {
  const router = useRouter();
  const t = useTranslations("services");
  const tc = useTranslations("common");
  const accessToken = useAuthStore((state) => state.accessToken);
  const workspaceId = useAuthStore((state) => state.workspaceId);

  useEffect(() => {
    if (!accessToken) router.replace("/login");
  }, [accessToken, router]);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["services", workspaceId],
    queryFn: () => apiFetch<ServiceList>("/api/v1/services"),
    enabled: Boolean(accessToken && workspaceId),
  });

  if (!accessToken) return null;

  const services = data?.data ?? [];

  return (
    <div className="min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-5xl px-6 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
            <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
          </div>
          <CreateServiceDialog />
        </div>

        {isLoading ? <p className="text-muted-foreground">{tc("loading")}</p> : null}
        {isError ? <p className="text-destructive">{t("loadError")}</p> : null}

        {!isLoading && !isError && services.length === 0 ? (
          <div className="rounded-lg border border-dashed p-10 text-center text-muted-foreground">
            {t("empty")}
          </div>
        ) : null}

        {services.length > 0 ? (
          <div className="rounded-lg border">
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
                {services.map((service) => (
                  <TableRow key={service.id}>
                    <TableCell className="font-medium">{service.name}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{t("tierLabel", { tier: service.tier })}</Badge>
                    </TableCell>
                    <TableCell className="max-w-xs truncate text-muted-foreground">
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
