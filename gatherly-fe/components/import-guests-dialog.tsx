"use client";

import { useQueryClient } from "@tanstack/react-query";
import { Upload } from "lucide-react";
import { useTranslations } from "next-intl";
import { useRef, useState } from "react";
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
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiFetch, type Data } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type ImportResult = components["schemas"]["GuestImportResponse"];

export function ImportGuestsDialog({ eventId }: { eventId: string }) {
  const t = useTranslations("detail.import");
  const tc = useTranslations("common");
  const tb = useTranslations("billing");
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [csv, setCsv] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const onFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    void file.text().then(setCsv);
  };

  const onSubmit = async () => {
    if (!csv.trim()) return;
    setSubmitting(true);
    try {
      const res = await apiFetch<Data<ImportResult>>(`/api/v1/events/${eventId}/guests/import`, {
        method: "POST",
        body: { csv },
      });
      const { created, skipped_duplicate, skipped_invalid } = res.data;
      toast.success(t("result", { created, duplicate: skipped_duplicate, invalid: skipped_invalid }));
      setCsv("");
      setOpen(false);
      await queryClient.invalidateQueries({ queryKey: ["guests", eventId] });
    } catch (error) {
      if (error instanceof ApiError && error.status === 402) {
        toast.error(tb("proRequired"));
      } else {
        toast.error(t("failed"));
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Upload className="mr-2 h-4 w-4" />
          {t("trigger")}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
          <DialogDescription>{t("description")}</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <Textarea
            value={csv}
            onChange={(event) => setCsv(event.target.value)}
            placeholder={"name,email\nAlex Rivera,alex@example.com"}
            rows={7}
            className="font-mono text-xs"
          />
          <div>
            <input
              ref={fileRef}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={onFile}
            />
            <Button type="button" variant="ghost" size="sm" onClick={() => fileRef.current?.click()}>
              {t("uploadFile")}
            </Button>
          </div>
        </div>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => setOpen(false)}>
            {tc("cancel")}
          </Button>
          <Button type="button" disabled={submitting || !csv.trim()} onClick={onSubmit}>
            {submitting ? t("importing") : t("import")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
