"use client";

import { useTranslations } from "next-intl";

import { SeverityBadge } from "@/components/severity-badge";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { components } from "@/lib/api/schema";
import { cn } from "@/lib/utils";

type Finding = components["schemas"]["FindingResponse"];

// Left rail color per severity — a quick scan cue beside the badge.
const RAIL: Record<string, string> = {
  critical: "border-l-severity-critical",
  high: "border-l-severity-high",
  medium: "border-l-severity-medium",
  low: "border-l-border",
};

export function FindingsTable({
  findings,
  nameById,
  showService = true,
}: {
  findings: Finding[];
  nameById: Map<string, string>;
  showService?: boolean;
}) {
  const t = useTranslations("findings");

  return (
    <div className="overflow-hidden rounded-xl border bg-card shadow-card">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t("columns.severity")}</TableHead>
            {showService ? <TableHead>{t("columns.service")}</TableHead> : null}
            <TableHead>{t("columns.criterion")}</TableHead>
            <TableHead>{t("columns.remediation")}</TableHead>
            <TableHead>{t("columns.autoFixable")}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {findings.map((finding) => (
            <TableRow key={finding.id}>
              <TableCell className={cn("border-l-[3px]", RAIL[finding.severity] ?? RAIL.low)}>
                <SeverityBadge severity={finding.severity} />
              </TableCell>
              {showService ? (
                <TableCell className="font-medium">
                  {nameById.get(finding.service_id) ?? finding.service_id}
                </TableCell>
              ) : null}
              <TableCell className="font-mono text-xs">{finding.criterion_id}</TableCell>
              <TableCell className="max-w-md text-muted-foreground">
                {finding.remediation}
              </TableCell>
              <TableCell>
                {finding.auto_fixable ? (
                  <Badge variant="outline">{t("autoFixable")}</Badge>
                ) : (
                  "—"
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
