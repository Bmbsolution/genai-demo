"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  CalendarDays,
  Check,
  Copy,
  Download,
  MapPin,
  Search,
  Send,
  Users,
} from "lucide-react";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { AppHeader } from "@/components/app-header";
import { EventInsights } from "@/components/event-insights";
import { ImportGuestsDialog } from "@/components/import-guests-dialog";
import { InviteGuestDialog } from "@/components/invite-guest-dialog";
import { RsvpBadge } from "@/components/rsvp-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { API_BASE, ApiError, apiFetch, type Data } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { formatEventDate } from "@/lib/format-date";
import { useAuthStore } from "@/lib/store/auth";

type Event = components["schemas"]["EventResponse"];
type Guest = components["schemas"]["GuestResponse"];
type ReminderResult = components["schemas"]["ReminderResponse"];

const RSVP_ORDER = ["yes", "maybe", "no", "pending"] as const;
const FILTERS = ["all", "yes", "maybe", "no", "pending"] as const;
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
  const queryClient = useQueryClient();
  const enabled = ready && Boolean(workspaceId);

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("all");
  const [exporting, setExporting] = useState(false);

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

  const checkIn = useMutation({
    mutationFn: ({ guestId, checkedIn }: { guestId: string; checkedIn: boolean }) =>
      apiFetch<Data<Guest>>(`/api/v1/events/${eventId}/guests/${guestId}/check-in`, {
        method: "PATCH",
        body: { checked_in: checkedIn },
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["guests", eventId] }),
    onError: () => toast.error(t("detail.guests.checkInFailed")),
  });

  const remind = useMutation({
    mutationFn: () =>
      apiFetch<Data<ReminderResult>>(`/api/v1/events/${eventId}/reminders`, { method: "POST" }),
    onSuccess: (res) => toast.success(t("detail.remindResult", { sent: res.data.sent })),
    onError: (error) =>
      toast.error(
        error instanceof ApiError && error.status === 402
          ? t("billing.proRequired")
          : t("detail.remindFailed"),
      ),
  });

  const rows = useMemo(() => guests.data ?? [], [guests.data]);
  const counts = useMemo(
    () =>
      rows.reduce<Record<string, number>>((acc, guest) => {
        acc[guest.rsvp_status] = (acc[guest.rsvp_status] ?? 0) + 1;
        return acc;
      }, {}),
    [rows],
  );
  const checkedInCount = useMemo(() => rows.filter((g) => g.checked_in_at).length, [rows]);

  const visibleRows = useMemo(() => {
    const term = search.trim().toLowerCase();
    return rows.filter((guest) => {
      if (filter !== "all" && guest.rsvp_status !== filter) return false;
      if (!term) return true;
      return (
        guest.name.toLowerCase().includes(term) || guest.email.toLowerCase().includes(term)
      );
    });
  }, [rows, search, filter]);

  if (!ready) return null;

  const copyInviteLink = (token: string) => {
    const url = `${window.location.origin}/rsvp/${token}`;
    void navigator.clipboard.writeText(url).then(
      () => toast.success(t("detail.guests.linkCopied")),
      () => toast.error(t("common.error")),
    );
  };

  const exportCsv = async () => {
    setExporting(true);
    try {
      const token = useAuthStore.getState().accessToken;
      const res = await fetch(`${API_BASE}/api/v1/events/${eventId}/guests/export`, {
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...(workspaceId ? { "X-Workspace-Id": workspaceId } : {}),
        },
      });
      if (!res.ok) throw new Error("export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${event.data?.title.replace(/\s+/g, "-").toLowerCase() ?? "guests"}.csv`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error(t("detail.exportFailed"));
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-5xl space-y-8 px-4 py-8 sm:px-6">
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
              {event.data.cover_image_url ? (
                <div
                  className="mb-4 h-44 w-full overflow-hidden rounded-2xl border bg-muted bg-cover bg-center"
                  style={{ backgroundImage: `url(${event.data.cover_image_url})` }}
                  role="img"
                  aria-label={event.data.title}
                />
              ) : null}
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="font-display text-3xl font-semibold tracking-tight">
                  {event.data.title}
                </h1>
                <Badge variant={event.data.status === "published" ? "brand" : "outline"}>
                  {t(`events.status.${event.data.status}`)}
                </Badge>
                <Badge variant="secondary">
                  {t(`events.visibility.${event.data.visibility}`)}
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
                {event.data.ends_at ? (
                  <span className="inline-flex items-center gap-2">
                    {t("detail.ends")} {formatEventDate(event.data.ends_at)}
                  </span>
                ) : null}
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

            <EventInsights eventId={eventId} enabled={enabled} />

            <Card className="animate-fade-up [animation-delay:60ms]">
              <CardHeader className="flex-row flex-wrap items-center justify-between gap-2 space-y-0">
                <CardTitle className="text-base">{t("detail.guests.title")}</CardTitle>
                <div className="flex flex-wrap items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={remind.isPending}
                    onClick={() => remind.mutate()}
                  >
                    <Send className="mr-2 h-4 w-4" />
                    {remind.isPending ? t("detail.reminding") : t("detail.remind")}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={exporting || rows.length === 0}
                    onClick={() => void exportCsv()}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    {t("detail.export")}
                  </Button>
                  <ImportGuestsDialog eventId={eventId} />
                  <InviteGuestDialog eventId={eventId} />
                </div>
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
                    {checkedInCount > 0 ? (
                      <span className="inline-flex items-center gap-1.5">
                        <Check className="h-3.5 w-3.5 text-success" />
                        <span className="text-muted-foreground">
                          {t("detail.checkedInCount", { count: checkedInCount })}
                        </span>
                      </span>
                    ) : null}
                  </div>
                ) : null}

                {rows.length > 0 ? (
                  <div className="flex flex-wrap items-center gap-2">
                    <div className="relative flex-1 min-w-[12rem]">
                      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        value={search}
                        onChange={(event_) => setSearch(event_.target.value)}
                        placeholder={t("detail.search")}
                        className="pl-9"
                      />
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {FILTERS.map((value) => (
                        <Button
                          key={value}
                          size="sm"
                          variant={filter === value ? "default" : "outline"}
                          onClick={() => setFilter(value)}
                        >
                          {value === "all" ? t("detail.filterAll") : t(`rsvp.status.${value}`)}
                        </Button>
                      ))}
                    </div>
                  </div>
                ) : null}

                {guests.isError ? (
                  <p className="text-sm text-destructive">{t("detail.guests.loadError")}</p>
                ) : rows.length === 0 ? (
                  <p className="text-sm text-muted-foreground">{t("detail.guests.empty")}</p>
                ) : visibleRows.length === 0 ? (
                  <p className="text-sm text-muted-foreground">{t("detail.guests.noMatch")}</p>
                ) : (
                  <div className="overflow-hidden rounded-xl border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>{t("detail.guests.name")}</TableHead>
                          <TableHead className="hidden md:table-cell">
                            {t("detail.guests.email")}
                          </TableHead>
                          <TableHead>{t("detail.guests.rsvp")}</TableHead>
                          <TableHead className="hidden sm:table-cell">
                            {t("detail.guests.plusOne")}
                          </TableHead>
                          <TableHead className="hidden lg:table-cell">
                            {t("detail.guests.dietary")}
                          </TableHead>
                          <TableHead>{t("detail.guests.checkedIn")}</TableHead>
                          <TableHead className="text-right">{t("detail.guests.invite")}</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {visibleRows.map((guest) => (
                          <TableRow key={guest.id}>
                            <TableCell className="font-medium">
                              {guest.name}
                              <span className="block truncate text-xs font-normal text-muted-foreground md:hidden">
                                {guest.email}
                              </span>
                            </TableCell>
                            <TableCell className="hidden text-muted-foreground md:table-cell">
                              {guest.email}
                            </TableCell>
                            <TableCell>
                              <RsvpBadge status={guest.rsvp_status} />
                            </TableCell>
                            <TableCell className="hidden tabular-nums sm:table-cell">
                              {guest.plus_one ? "+1" : "—"}
                            </TableCell>
                            <TableCell className="hidden max-w-[12rem] truncate text-muted-foreground lg:table-cell">
                              {guest.dietary_notes ?? "—"}
                            </TableCell>
                            <TableCell>
                              <Button
                                size="sm"
                                variant={guest.checked_in_at ? "default" : "outline"}
                                disabled={checkIn.isPending}
                                onClick={() =>
                                  checkIn.mutate({
                                    guestId: guest.id,
                                    checkedIn: !guest.checked_in_at,
                                  })
                                }
                              >
                                <Check className="mr-1.5 h-3.5 w-3.5" />
                                {guest.checked_in_at
                                  ? t("detail.guests.checkedIn")
                                  : t("detail.guests.checkIn")}
                              </Button>
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
