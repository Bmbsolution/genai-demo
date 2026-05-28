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

type Finding = components["schemas"]["FindingResponse"];

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
    <div className="rounded-lg border">
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
              <TableCell>
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
