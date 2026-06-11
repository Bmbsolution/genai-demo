"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api/client";

const schema = z.object({
  title: z.string().min(1),
  starts_at: z.string().min(1),
  location: z.string().optional(),
  capacity: z.number().int().min(1).max(100000).optional(),
  description: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;

export function CreateEventDialog() {
  const t = useTranslations();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const {
    register,
    handleSubmit,
    reset,
    formState: { isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = handleSubmit(async (values) => {
    try {
      const body = {
        title: values.title,
        // datetime-local has no timezone — interpret as local and send ISO/UTC.
        starts_at: new Date(values.starts_at).toISOString(),
        location: values.location?.trim() || undefined,
        capacity: values.capacity ?? undefined,
        description: values.description?.trim() || undefined,
      };
      await apiFetch("/api/v1/events", { method: "POST", body });
      toast.success(t("events.dialog.created"));
      reset();
      setOpen(false);
      await queryClient.invalidateQueries({ queryKey: ["events"] });
    } catch {
      toast.error(t("events.dialog.failed"));
    }
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          {t("events.new")}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("events.dialog.title")}</DialogTitle>
          <DialogDescription>{t("events.dialog.description")}</DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">{t("events.dialog.name")}</Label>
            <Input id="title" placeholder="Team Offsite 2026" {...register("title")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="starts_at">{t("events.dialog.startsAt")}</Label>
            <Input id="starts_at" type="datetime-local" {...register("starts_at")} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="location">{t("events.dialog.location")}</Label>
              <Input id="location" placeholder="Mont-Tremblant" {...register("location")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="capacity">{t("events.dialog.capacity")}</Label>
              <Input
                id="capacity"
                type="number"
                min={1}
                {...register("capacity", { setValueAs: (v) => (v === "" ? undefined : Number(v)) })}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">{t("events.dialog.descriptionField")}</Label>
            <Input id="description" {...register("description")} />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? t("events.dialog.submitting") : t("events.dialog.submit")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
