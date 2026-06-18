"use client";

import { useQuery } from "@tanstack/react-query";
import { CalendarDays, MapPin, PartyPopper, Users } from "lucide-react";
import { useTranslations } from "next-intl";
import Link from "next/link";

import { AppHeader } from "@/components/app-header";
import { Confetti } from "@/components/confetti";
import { CreateEventDialog } from "@/components/create-event-dialog";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { formatEventDate } from "@/lib/format-date";
import { useAuthStore } from "@/lib/store/auth";

type EventList = components["schemas"]["EventListResponse"];

export default function EventsPage() {
  const { ready } = useRequireAuth();
  const t = useTranslations("events");
  const tc = useTranslations("common");
  const userId = useAuthStore((state) => state.userId);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["events", userId],
    queryFn: () => apiFetch<EventList>("/api/v1/events"),
    enabled: ready && Boolean(userId),
  });

  if (!ready) return null;

  const events = data?.data ?? [];

  return (
    <div className="min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h1 className="font-display text-3xl font-semibold tracking-tight">{t("title")}</h1>
              {events.length > 0 ? (
                <Badge variant="secondary" className="font-mono">
                  {events.length}
                </Badge>
              ) : null}
            </div>
            <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
          </div>
          <CreateEventDialog />
        </div>

        {isLoading ? <p className="text-muted-foreground">{tc("loading")}</p> : null}
        {isError ? <p className="text-destructive">{t("loadError")}</p> : null}

        {!isLoading && !isError && events.length === 0 ? (
          <div className="animate-fade-up flex flex-col items-center gap-3 rounded-2xl border border-dashed bg-card/40 p-12 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand/10 text-brand">
              <PartyPopper className="h-6 w-6" aria-hidden="true" />
            </span>
            <p className="text-sm text-muted-foreground">{t("empty")}</p>
            <CreateEventDialog />
          </div>
        ) : null}

        {events.length > 0 ? (
          <div className="grid gap-5 sm:grid-cols-2">
            {events.map((event, i) => (
              <Link
                key={event.id}
                href={`/events/${event.id}`}
                className="group animate-fade-up block rounded-2xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <Card className="h-full overflow-hidden p-0 transition-all duration-300 group-hover:-translate-y-1 group-hover:border-brand/30 group-hover:shadow-lift">
                  <div
                    className="relative h-24 bg-brand bg-cover bg-center"
                    style={
                      event.cover_image_url
                        ? { backgroundImage: `url(${event.cover_image_url})` }
                        : undefined
                    }
                  >
                    {event.cover_image_url ? null : <Confetti />}
                    <span className="absolute left-3 top-3 inline-flex items-center gap-1.5 rounded-full bg-white/15 px-2.5 py-1 text-xs font-semibold text-white backdrop-blur-sm">
                      <span className="h-1.5 w-1.5 rounded-full bg-white" />
                      {t(`status.${event.status}`)}
                    </span>
                    {event.capacity ? (
                      <span className="absolute right-3 top-3 inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-1 text-xs font-semibold text-white backdrop-blur-sm">
                        <Users className="h-3.5 w-3.5" />
                        {event.capacity}
                      </span>
                    ) : null}
                  </div>
                  <div className="p-5">
                    <h2 className="font-display text-lg font-semibold tracking-tight transition-colors group-hover:text-brand">
                      {event.title}
                    </h2>
                    <div className="mt-2 space-y-1.5 text-sm text-muted-foreground">
                      <p className="inline-flex items-center gap-2">
                        <CalendarDays className="h-4 w-4 shrink-0" />
                        {formatEventDate(event.starts_at)}
                      </p>
                      <p className="inline-flex items-center gap-2">
                        <MapPin className="h-4 w-4 shrink-0" />
                        {event.location ?? t("noLocation")}
                      </p>
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        ) : null}
      </main>
    </div>
  );
}
