"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { PlayCircle } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiFetch, type Data } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type Run = components["schemas"]["ScorecardRunResponse"];

const ACTIVE_STATUSES = new Set(["queued", "running"]);

export function RunScorecardButton({ serviceId }: { serviceId: string }) {
  const t = useTranslations();
  const [runId, setRunId] = useState<string | null>(null);

  const trigger = useMutation({
    mutationFn: () =>
      apiFetch<Data<Run>>("/api/v1/scorecards/documentation/runs", {
        method: "POST",
        body: { target_service_ids: [serviceId] },
      }).then((res) => res.data),
    onSuccess: (run) => setRunId(run.id),
    onError: () => toast.error(t("common.error")),
  });

  const { data: run } = useQuery({
    queryKey: ["run", runId],
    queryFn: () =>
      apiFetch<Data<Run>>(`/api/v1/scorecards/runs/${runId}`).then((res) => res.data),
    enabled: Boolean(runId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && ACTIVE_STATUSES.has(status) ? 1500 : false;
    },
  });

  const isBusy = trigger.isPending || Boolean(run && ACTIVE_STATUSES.has(run.status));

  return (
    <div className="flex flex-wrap items-center gap-3">
      <Button size="sm" onClick={() => trigger.mutate()} disabled={isBusy}>
        <PlayCircle className="mr-2 h-4 w-4" />
        {isBusy ? t("detail.scorecard.running") : t("detail.scorecard.run")}
      </Button>
      {run ? (
        <Badge variant={run.status === "failed" ? "destructive" : "secondary"}>{run.status}</Badge>
      ) : null}
      {run?.status === "completed" ? (
        <span className="text-sm text-muted-foreground">
          {t("detail.scorecard.findings", { count: run.finding_count })}
        </span>
      ) : null}
      {run?.status === "failed" && run.error ? (
        <span className="text-sm text-destructive">
          {t("detail.scorecard.failed", { error: run.error })}
        </span>
      ) : null}
    </div>
  );
}
