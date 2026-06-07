"use client";

import { useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type Service = components["schemas"]["ServiceResponse"];

export function AddDependencyDialog({
  serviceId,
  candidates,
}: {
  serviceId: string;
  candidates: Service[];
}) {
  const t = useTranslations();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [target, setTarget] = useState("");
  const [criticality, setCriticality] = useState("hard");
  const [direction, setDirection] = useState("consumes");
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async () => {
    if (!target) return;
    setSubmitting(true);
    try {
      await apiFetch(`/api/v1/services/${serviceId}/dependencies`, {
        method: "POST",
        body: { depends_on_service_id: target, criticality, direction },
      });
      toast.success(t("detail.dependencies.created"));
      setTarget("");
      setOpen(false);
      await queryClient.invalidateQueries({ queryKey: ["dependencies", serviceId] });
    } catch {
      toast.error(t("detail.dependencies.failed"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline" disabled={candidates.length === 0}>
          <Plus className="mr-2 h-4 w-4" />
          {t("detail.dependencies.add")}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("detail.dependencies.add")}</DialogTitle>
          <DialogDescription>{t("detail.dependencies.addDescription")}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>{t("detail.dependencies.target")}</Label>
            <Select value={target} onValueChange={setTarget}>
              <SelectTrigger>
                <SelectValue placeholder="—" />
              </SelectTrigger>
              <SelectContent>
                {candidates.map((candidate) => (
                  <SelectItem key={candidate.id} value={candidate.id}>
                    {candidate.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>{t("detail.dependencies.criticality")}</Label>
            <Select value={criticality} onValueChange={setCriticality}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="hard">{t("detail.dependencies.criticalityOptions.hard")}</SelectItem>
                <SelectItem value="soft">{t("detail.dependencies.criticalityOptions.soft")}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>{t("detail.dependencies.direction")}</Label>
            <Select value={direction} onValueChange={setDirection}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="consumes">{t("detail.dependencies.directionOptions.consumes")}</SelectItem>
                <SelectItem value="produces">{t("detail.dependencies.directionOptions.produces")}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              {t("common.cancel")}
            </Button>
            <Button onClick={onSubmit} disabled={submitting || !target}>
              {t("detail.dependencies.submit")}
            </Button>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  );
}
