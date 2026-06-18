"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarDays, CalendarPlus, MapPin, PartyPopper } from "lucide-react";
import { useTranslations } from "next-intl";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Confetti } from "@/components/confetti";
import { RsvpBadge } from "@/components/rsvp-badge";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch, type Data } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { formatEventDate } from "@/lib/format-date";

type RsvpView = components["schemas"]["RsvpView"];
type RsvpEvent = RsvpView["event"];

const CHOICES = ["yes", "maybe", "no"] as const;

function escapeIcs(value: string): string {
  return value.replace(/([,;\\])/g, "\\$1").replace(/\n/g, " ");
}

function toIcsDate(iso: string): string {
  return new Date(iso).toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
}

function downloadIcs(event: RsvpEvent): void {
  const start = toIcsDate(event.starts_at);
  const end = event.ends_at ? toIcsDate(event.ends_at) : start;
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Gatherly//EN",
    "BEGIN:VEVENT",
    `DTSTART:${start}`,
    `DTEND:${end}`,
    `SUMMARY:${escapeIcs(event.title)}`,
    event.location ? `LOCATION:${escapeIcs(event.location)}` : "",
    event.description ? `DESCRIPTION:${escapeIcs(event.description)}` : "",
    "END:VEVENT",
    "END:VCALENDAR",
  ].filter(Boolean);
  const blob = new Blob([lines.join("\r\n")], { type: "text/calendar" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${event.title.replace(/\s+/g, "-").toLowerCase()}.ics`;
  link.click();
  URL.revokeObjectURL(url);
}

export default function RsvpPage() {
  const params = useParams<{ token: string }>();
  const token = params.token;
  const t = useTranslations("rsvp");
  const tc = useTranslations("common");
  const queryClient = useQueryClient();

  const rsvp = useQuery({
    queryKey: ["rsvp", token],
    queryFn: () =>
      apiFetch<Data<RsvpView>>(`/api/v1/rsvp/${token}`, { auth: false }).then((res) => res.data),
    retry: false,
  });

  const [plusOne, setPlusOne] = useState(false);
  const [dietary, setDietary] = useState("");

  useEffect(() => {
    if (rsvp.data) {
      setPlusOne(rsvp.data.plus_one);
      setDietary(rsvp.data.dietary_notes ?? "");
    }
  }, [rsvp.data]);

  const respond = useMutation({
    mutationFn: (status: string) =>
      apiFetch<Data<RsvpView>>(`/api/v1/rsvp/${token}`, {
        method: "POST",
        body: { rsvp_status: status, plus_one: plusOne, dietary_notes: dietary.trim() || null },
        auth: false,
      }).then((res) => res.data),
    onSuccess: (data) => {
      queryClient.setQueryData(["rsvp", token], data);
      toast.success(t("saved"));
    },
    onError: () => toast.error(tc("error")),
  });

  const view = rsvp.data;

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden p-6">
      <div className="bg-dots pointer-events-none absolute inset-0 [mask-image:radial-gradient(ellipse_60%_50%_at_50%_40%,black,transparent)]" />
      <span className="halo bg-brand/20" style={{ width: 360, height: 360, top: -120, left: -80 }} />
      <span className="halo bg-gold/10" style={{ width: 280, height: 280, bottom: -80, right: -50 }} />
      <div className="absolute right-4 top-4 z-10">
        <ThemeToggle />
      </div>
      <Card className="animate-fade-up relative z-10 w-full max-w-md overflow-hidden border-border/60 shadow-lift">
        {view ? (
          <div
            className="relative h-28 w-full bg-brand bg-cover bg-center"
            style={
              view.event.cover_image_url
                ? { backgroundImage: `url(${view.event.cover_image_url})` }
                : undefined
            }
            role="img"
            aria-label={view.event.title}
          >
            {view.event.cover_image_url ? null : (
              <>
                <Confetti />
                <span className="absolute bottom-3 left-6 flex h-10 w-10 items-center justify-center rounded-xl bg-white/15 backdrop-blur-sm">
                  <PartyPopper className="h-5 w-5 text-white" aria-hidden="true" />
                </span>
              </>
            )}
          </div>
        ) : null}
        <CardContent className="space-y-6 p-8">
          {rsvp.isLoading ? <p className="text-muted-foreground">{tc("loading")}</p> : null}
          {rsvp.isError ? (
            <div className="space-y-2 text-center">
              <h1 className="font-display text-xl font-semibold">{t("notFoundTitle")}</h1>
              <p className="text-sm text-muted-foreground">{t("notFound")}</p>
            </div>
          ) : null}

          {view ? (
            <>
              <div className="space-y-3">
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
                <Button variant="outline" size="sm" onClick={() => downloadIcs(view.event)}>
                  <CalendarPlus className="mr-1.5 h-4 w-4" />
                  {t("addToCalendar")}
                </Button>
              </div>

              <div className="space-y-4 border-t border-border/60 pt-5">
                <div className="flex items-center justify-between">
                  <p className="text-sm">{t("greeting", { name: view.guest_name })}</p>
                  <RsvpBadge status={view.rsvp_status} />
                </div>

                <label className="flex items-center gap-2.5 text-sm">
                  <input
                    type="checkbox"
                    className="h-4 w-4 accent-brand"
                    checked={plusOne}
                    onChange={(e) => setPlusOne(e.target.checked)}
                  />
                  {t("plusOneLabel")}
                </label>

                <div className="space-y-2">
                  <Label htmlFor="dietary">{t("dietaryLabel")}</Label>
                  <Input
                    id="dietary"
                    value={dietary}
                    maxLength={500}
                    onChange={(e) => setDietary(e.target.value)}
                  />
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

                {view.rsvp_status === "waitlisted" ? (
                  <p className="rounded-lg border border-brand/30 bg-brand/10 px-3 py-2 text-sm text-brand">
                    {t("waitlistedNote")}
                  </p>
                ) : null}
              </div>
            </>
          ) : null}
        </CardContent>
      </Card>
    </main>
  );
}
