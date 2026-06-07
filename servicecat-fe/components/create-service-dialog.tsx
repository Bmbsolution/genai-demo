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
  name: z.string().min(1),
  repo_url: z.string().min(1),
  tier: z.number().int().min(1).max(3),
  description: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;

export function CreateServiceDialog() {
  const t = useTranslations();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const {
    register,
    handleSubmit,
    reset,
    formState: { isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { tier: 2 } });

  const onSubmit = handleSubmit(async (values) => {
    try {
      // An untouched description field submits "" — omit it so the API stores
      // NULL (the list view renders its "—" fallback only for null/undefined).
      const body = { ...values, description: values.description?.trim() || undefined };
      await apiFetch("/api/v1/services", { method: "POST", body });
      toast.success(t("services.dialog.created"));
      reset({ tier: 2 });
      setOpen(false);
      await queryClient.invalidateQueries({ queryKey: ["services"] });
    } catch {
      toast.error(t("services.dialog.failed"));
    }
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          {t("services.new")}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("services.dialog.title")}</DialogTitle>
          <DialogDescription>{t("services.dialog.description")}</DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">{t("services.dialog.name")}</Label>
            <Input id="name" {...register("name")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="repo_url">{t("services.dialog.repoUrl")}</Label>
            <Input id="repo_url" placeholder="https://github.com/acme/payments" {...register("repo_url")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="tier">{t("services.dialog.tier")}</Label>
            <Input
              id="tier"
              type="number"
              min={1}
              max={3}
              {...register("tier", { valueAsNumber: true })}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">{t("services.dialog.descriptionField")}</Label>
            <Input id="description" {...register("description")} />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? t("services.dialog.submitting") : t("services.dialog.submit")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
