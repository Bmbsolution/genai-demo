"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, CalendarDays, Copy, MapPin, Users } from "lucide-react";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useParams } from "next/navigation";
import { toast } from "sonner";

import { AppHeader } from "@/components/app-header";
import { InviteGuestDialog } from "@/components/invite-guest-dialog";
import { RsvpBadge } from "@/components/rsvp-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { apiFetch, type Data } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { formatEventDate } from "@/lib/format-date";
import { useAuthStore } from "@/lib/store/auth";

type Event = components["schemas"]["EventResponse"];
type Guest = components["schemas"]["GuestResponse"];

const RSVP_ORDER = ["yes", "maybe", "no", "pending"] as const;
const SUMMARY_DOT: Record<string, string> = {
  yes: "bg-success",
  maybe: "bg-warning",
  no: "bg-destructive",
  pending: "bg-muted-foreground",
};

export default function EventDetailPage() {
  const params = useParams<{ id: string }>();
  const eventId = params.id;
  const { ready } = useRequireAuth();
  const t = useTranslations();
  const workspaceId = useAuthStore((state) => state.workspaceId);
  const enabled = ready && Boolean(workspaceId);

  const event = useQuery({
    queryKey: ["event", eventId],
    queryFn: () => apiFetch<Data<Event>>(`/api/v1/events/${eventId}`).then((res) => res.data),
    enabled,
  });
  const guests = useQuery({
    queryKey: ["guests", eventId],
    queryFn: () =>
      apiFetch<Data<Guest[]>>(`/api/v1/events/${eventId}/guests`).then((res) => res.data),
    enabled,
  });

  if (!ready) return null;

  const rows = guests.data ?? [];
  const counts = rows.reduce<Record<string, number>>((acc, guest) => {
    acc[guest.rsvp_status] = (acc[guest.rsvp_status] ?? 0) + 1;
    return acc;
  }, {});

  const copyInviteLink = (token: string) => {
    const url = `${window.location.origin}/rsvp/${token}`;
    void navigator.clipboard.writeText(url).then(
      () => toast.success(t("detail.guests.linkCopied")),
      () => toast.error(t("common.error")),
    );
  };

  return (
    <div className="min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-5xl space-y-8 px-6 py-8">
        <Link
          href="/events"
          className="inline-flex items-center text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="mr-1 h-4 w-4" />
          {t("detail.back")}
        </Link>

        {event.isError ? <p className="text-destructive">{t("detail.notFound")}</p> : null}

        {event.data ? (
          <>
            <div className="animate-fade-up">
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="font-display text-3xl font-semibold tracking-tight">
                  {event.data.title}
                </h1>
                <Badge variant={event.data.status === "published" ? "brand" : "outline"}>
                  {t(`events.status.${event.data.status}`)}
                </Badge>
              </div>
              {event.data.description ? (
                <p className="mt-1 text-muted-foreground">{event.data.description}</p>
              ) : null}
              <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1.5 text-sm text-muted-foreground">
                <span className="inline-flex items-center gap-2">
                  <CalendarDays className="h-4 w-4" />
                  {formatEventDate(event.data.starts_at)}
                </span>
                <span className="inline-flex items-center gap-2">
                  <MapPin className="h-4 w-4" />
                  {event.data.location ?? t("events.noLocation")}
                </span>
                {event.data.capacity ? (
                  <span className="inline-flex items-center gap-2">
                    <Users className="h-4 w-4" />
                    {t("detail.spots", { yes: counts.yes ?? 0, capacity: event.data.capacity })}
                  </span>
                ) : null}
              </div>
            </div>

            <Card className="animate-fade-up [animation-delay:60ms]">
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <CardTitle className="text-base">{t("detail.guests.title")}</CardTitle>
                <InviteGuestDialog eventId={eventId} />
              </CardHeader>
              <CardContent className="space-y-4">
                {rows.length > 0 ? (
                  <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
                    {RSVP_ORDER.filter((status) => counts[status]).map((status) => (
                      <span key={status} className="inline-flex items-center gap-1.5">
                        <span className={`h-2 w-2 rounded-full ${SUMMARY_DOT[status]}`} />
                        <span className="font-semibold tabular-nums">{counts[status]}</span>
                        <span className="capitalize text-muted-foreground">
                          {t(`rsvp.status.${status}`)}
                        </span>
                      </span>
                    ))}
                  </div>
                ) : null}

                {guests.isError ? (
                  <p className="text-sm text-destructive">{t("detail.guests.loadError")}</p>
                ) : rows.length === 0 ? (
                  <p className="text-sm text-muted-foreground">{t("detail.guests.empty")}</p>
                ) : (
                  <div className="overflow-hidden rounded-xl border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>{t("detail.guests.name")}</TableHead>
                          <TableHead>{t("detail.guests.email")}</TableHead>
                          <TableHead>{t("detail.guests.rsvp")}</TableHead>
                          <TableHead className="text-right">{t("detail.guests.invite")}</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {rows.map((guest) => (
                          <TableRow key={guest.id}>
                            <TableCell className="font-medium">{guest.name}</TableCell>
                            <TableCell className="text-muted-foreground">{guest.email}</TableCell>
                            <TableCell>
                              <RsvpBadge status={guest.rsvp_status} />
                            </TableCell>
                            <TableCell className="text-right">
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => copyInviteLink(guest.invite_token)}
                              >
                                <Copy className="mr-1.5 h-3.5 w-3.5" />
                                {t("detail.guests.copyLink")}
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        ) : null}
      </main>
    </div>
  );
}
