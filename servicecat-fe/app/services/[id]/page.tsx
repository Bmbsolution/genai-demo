"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useParams } from "next/navigation";

import { AddDependencyDialog } from "@/components/add-dependency-dialog";
import { AppHeader } from "@/components/app-header";
import { FindingsTable } from "@/components/findings-table";
import { RunScorecardButton } from "@/components/run-scorecard-button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { apiFetch, type Data } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { useAuthStore } from "@/lib/store/auth";

type Service = components["schemas"]["ServiceResponse"];
type ServiceList = components["schemas"]["ServiceListResponse"];
type Dependency = components["schemas"]["ServiceDependencyResponse"];
type FindingList = components["schemas"]["FindingListResponse"];

export default function ServiceDetailPage() {
  const params = useParams<{ id: string }>();
  const serviceId = params.id;
  const { ready } = useRequireAuth();
  const t = useTranslations();
  const workspaceId = useAuthStore((state) => state.workspaceId);

  const enabled = ready && Boolean(workspaceId);
  const service = useQuery({
    queryKey: ["service", serviceId],
    queryFn: () =>
      apiFetch<Data<Service>>(`/api/v1/services/${serviceId}`).then((res) => res.data),
    enabled,
  });
  const dependencies = useQuery({
    queryKey: ["dependencies", serviceId],
    queryFn: () =>
      apiFetch<Data<Dependency[]>>(`/api/v1/services/${serviceId}/dependencies?depth=2`).then(
        (res) => res.data,
      ),
    enabled,
  });
  const allServices = useQuery({
    queryKey: ["services", workspaceId],
    queryFn: () => apiFetch<ServiceList>("/api/v1/services?limit=200"),
    enabled,
  });
  const findings = useQuery({
    queryKey: ["findings", workspaceId, serviceId],
    queryFn: () => apiFetch<FindingList>(`/api/v1/findings?service_id=${serviceId}`),
    enabled,
  });

  if (!ready) return null;

  const nameById = new Map((allServices.data?.data ?? []).map((item) => [item.id, item.name]));
  const candidates = (allServices.data?.data ?? []).filter((item) => item.id !== serviceId);
  const edges = dependencies.data ?? [];
  const serviceFindings = findings.data?.data ?? [];

  return (
    <div className="min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-5xl space-y-8 px-6 py-8">
        <Link
          href="/services"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="mr-1 h-4 w-4" />
          {t("detail.back")}
        </Link>

        {service.isError ? <p className="text-destructive">{t("detail.notFound")}</p> : null}

        {service.data ? (
          <>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-semibold tracking-tight">{service.data.name}</h1>
                <Badge variant="secondary">
                  {t("services.tierLabel", { tier: service.data.tier })}
                </Badge>
              </div>
              {service.data.description ? (
                <p className="mt-1 text-muted-foreground">{service.data.description}</p>
              ) : null}
              <p className="mt-1 text-sm text-muted-foreground">
                {t("detail.repo")}: {service.data.repo_url}
              </p>
            </div>

            <Card>
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <CardTitle className="text-base">{t("detail.dependencies.title")}</CardTitle>
                <AddDependencyDialog serviceId={serviceId} candidates={candidates} />
              </CardHeader>
              <CardContent>
                {edges.length === 0 ? (
                  <p className="text-sm text-muted-foreground">{t("detail.dependencies.empty")}</p>
                ) : (
                  <ul className="space-y-2">
                    {edges.map((edge) => (
                      <li key={edge.id} className="flex items-center gap-2 text-sm">
                        <Badge variant="outline">depth {edge.depth}</Badge>
                        <span className="font-medium">
                          {nameById.get(edge.depends_on_service_id) ?? edge.depends_on_service_id}
                        </span>
                        <span className="text-muted-foreground">
                          · {edge.criticality} · {edge.direction}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">{t("detail.scorecard.title")}</CardTitle>
                <p className="text-sm text-muted-foreground">{t("detail.scorecard.subtitle")}</p>
              </CardHeader>
              <CardContent>
                <RunScorecardButton serviceId={serviceId} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">{t("findings.onService")}</CardTitle>
              </CardHeader>
              <CardContent>
                {serviceFindings.length === 0 ? (
                  <p className="text-sm text-muted-foreground">{t("findings.empty")}</p>
                ) : (
                  <FindingsTable
                    findings={serviceFindings}
                    nameById={nameById}
                    showService={false}
                  />
                )}
              </CardContent>
            </Card>
          </>
        ) : null}
      </main>
    </div>
  );
}
