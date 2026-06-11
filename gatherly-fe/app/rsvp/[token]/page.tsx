"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarDays, MapPin, PartyPopper } from "lucide-react";
import { useTranslations } from "next-intl";
import { useParams } from "next/navigation";
import { toast } from "sonner";

import { RsvpBadge } from "@/components/rsvp-badge";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { apiFetch, type Data } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { formatEventDate } from "@/lib/format-date";

type RsvpView = components["schemas"]["RsvpView"];

const CHOICES = ["yes", "maybe", "no"] as const;

export default function RsvpPage() {
  const params = useParams<{ token: string }>();
  const token = params.token;
  const t = useTranslations("rsvp");
  const tc = useTranslations("common");
  const queryClient = useQueryClient();

  const rsvp = useQuery({
    queryKey: ["rsvp", token],
    queryFn: () =>
      apiFetch<Data<RsvpView>>(`/api/v1/rsvp/${token}`, { auth: false, workspace: false }).then(
        (res) => res.data,
      ),
    retry: false,
  });

  const respond = useMutation({
    mutationFn: (status: string) =>
      apiFetch<Data<RsvpView>>(`/api/v1/rsvp/${token}`, {
        method: "POST",
        body: { rsvp_status: status },
        auth: false,
        workspace: false,
      }).then((res) => res.data),
    onSuccess: (data) => {
      queryClient.setQueryData(["rsvp", token], data);
      toast.success(t("saved"));
    },
    onError: () => toast.error(tc("error")),
  });

  const view = rsvp.data;

  return (
    <main className="relative flex min-h-screen items-center justify-center bg-grid p-6">
      <div className="absolute right-4 top-4">
        <ThemeToggle />
      </div>
      <Card className="animate-fade-up w-full max-w-md border-border/70 p-8 shadow-xl">
        {rsvp.isLoading ? <p className="text-muted-foreground">{tc("loading")}</p> : null}
        {rsvp.isError ? (
          <div className="space-y-2 text-center">
            <h1 className="font-display text-xl font-semibold">{t("notFoundTitle")}</h1>
            <p className="text-sm text-muted-foreground">{t("notFound")}</p>
          </div>
        ) : null}

        {view ? (
          <CardContent className="space-y-6 p-0">
            <div className="space-y-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary">
                <PartyPopper className="h-5 w-5 text-primary-foreground" aria-hidden="true" />
              </span>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-brand">
                  {t("invited")}
                </p>
                <h1 className="font-display text-2xl font-semibold tracking-tight">
                  {view.event.title}
                </h1>
              </div>
              <div className="space-y-1.5 text-sm text-muted-foreground">
                <p className="inline-flex items-center gap-2">
                  <CalendarDays className="h-4 w-4 shrink-0" />
                  {formatEventDate(view.event.starts_at)}
                </p>
                {view.event.location ? (
                  <p className="inline-flex items-center gap-2">
                    <MapPin className="h-4 w-4 shrink-0" />
                    {view.event.location}
                  </p>
                ) : null}
              </div>
            </div>

            <div className="space-y-3 border-t border-border/60 pt-5">
              <div className="flex items-center justify-between">
                <p className="text-sm">
                  {t("greeting", { name: view.guest_name })}
                </p>
                <RsvpBadge status={view.rsvp_status} />
              </div>
              <div className="grid grid-cols-3 gap-2">
                {CHOICES.map((choice) => (
                  <Button
                    key={choice}
                    variant={view.rsvp_status === choice ? "default" : "outline"}
                    disabled={respond.isPending}
                    onClick={() => respond.mutate(choice)}
                  >
                    {t(`status.${choice}`)}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        ) : null}
      </Card>
    </main>
  );
}
