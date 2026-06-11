"use client";

import { useQuery } from "@tanstack/react-query";
import { CalendarDays, MapPin, PartyPopper, Users } from "lucide-react";
import { useTranslations } from "next-intl";
import Link from "next/link";

import { AppHeader } from "@/components/app-header";
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
  const workspaceId = useAuthStore((state) => state.workspaceId);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["events", workspaceId],
    queryFn: () => apiFetch<EventList>("/api/v1/events"),
    enabled: ready && Boolean(workspaceId),
  });

  if (!ready) return null;

  const events = data?.data ?? [];

  return (
    <div className="min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-5xl px-6 py-8">
        <div className="mb-6 flex items-end justify-between gap-4">
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
          <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed bg-card/40 p-12 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted text-muted-foreground">
              <PartyPopper className="h-6 w-6" aria-hidden="true" />
            </span>
            <p className="text-sm text-muted-foreground">{t("empty")}</p>
            <CreateEventDialog />
          </div>
        ) : null}

        {events.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {events.map((event, i) => (
              <Link
                key={event.id}
                href={`/events/${event.id}`}
                className="animate-fade-up rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                style={{ animationDelay: `${i * 50}ms` }}
              >
                <Card className="h-full p-5 transition-colors hover:border-brand/40">
                  <div className="mb-3 flex items-center justify-between gap-2">
                    <Badge variant={event.status === "published" ? "brand" : "outline"}>
                      {t(`status.${event.status}`)}
                    </Badge>
                    {event.capacity ? (
                      <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                        <Users className="h-3.5 w-3.5" />
                        {event.capacity}
                      </span>
                    ) : null}
                  </div>
                  <h2 className="font-display text-lg font-semibold tracking-tight">{event.title}</h2>
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
                </Card>
              </Link>
            ))}
          </div>
        ) : null}
      </main>
    </div>
  );
}
