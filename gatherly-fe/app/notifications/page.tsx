"use client";

import {
  Bell,
  Check,
  CheckCheck,
  ClipboardCheck,
  Info,
  Inbox,
  UserCheck,
  UserPlus,
  type LucideIcon,
} from "lucide-react";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useState } from "react";

import { AppHeader } from "@/components/app-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
} from "@/hooks/use-notifications";
import { useRequireAuth } from "@/hooks/use-require-auth";
import type { components } from "@/lib/api/schema";
import { formatRelativeTime } from "@/lib/format-date";
import { cn } from "@/lib/utils";

type Notification = components["schemas"]["NotificationResponse"];
type Filter = "all" | "unread";

/** Icon per notification type; unknown types fall back to the system bell. */
const TYPE_ICON: Record<string, LucideIcon> = {
  "guest.rsvp": UserPlus,
  "guest.checked_in": UserCheck,
  "event.readiness": ClipboardCheck,
  system: Info,
};

function NotificationRow({
  notification,
  onMarkRead,
  isMarking,
}: {
  notification: Notification;
  onMarkRead: (id: string) => void;
  isMarking: boolean;
}) {
  const t = useTranslations("notifications");
  const Icon = TYPE_ICON[notification.type] ?? Bell;
  const unread = notification.read_at === null;

  return (
    <Card
      className={cn(
        "animate-fade-up flex items-start gap-3 p-4 transition-colors",
        unread ? "border-brand/30 bg-brand/[0.03]" : "bg-card/40",
      )}
    >
      <span
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl",
          unread ? "bg-brand/10 text-brand" : "bg-muted text-muted-foreground",
        )}
      >
        <Icon className="h-[18px] w-[18px]" aria-hidden="true" />
      </span>

      <div className="min-w-0 flex-1">
        <div className="flex items-start gap-2">
          <p className="min-w-0 flex-1 text-sm font-medium leading-snug">{notification.title}</p>
          {unread ? (
            <span
              className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-brand"
              aria-label={t("unread")}
            />
          ) : null}
        </div>
        {notification.body ? (
          <p className="mt-1 text-sm text-muted-foreground">{notification.body}</p>
        ) : null}
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
          <time dateTime={notification.created_at}>
            {formatRelativeTime(notification.created_at)}
          </time>
          {notification.event_id ? (
            <Link
              href={`/events/${notification.event_id}`}
              className="font-medium text-brand hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              {t("viewEvent")}
            </Link>
          ) : null}
          {unread ? (
            <Button
              variant="ghost"
              size="sm"
              className="-my-1 ml-auto h-auto px-2 py-1 text-xs"
              onClick={() => onMarkRead(notification.id)}
              disabled={isMarking}
            >
              <Check className="mr-1 h-3.5 w-3.5" aria-hidden="true" />
              {t("markRead")}
            </Button>
          ) : null}
        </div>
      </div>
    </Card>
  );
}

export default function NotificationsPage() {
  const { ready } = useRequireAuth();
  const t = useTranslations("notifications");
  const tc = useTranslations("common");
  const [filter, setFilter] = useState<Filter>("all");

  const { data, isLoading, isError, hasNextPage, fetchNextPage, isFetchingNextPage } =
    useNotifications({
      unreadOnly: filter === "unread",
      enabled: ready,
    });
  const markRead = useMarkNotificationRead();
  const markAll = useMarkAllNotificationsRead();

  if (!ready) return null;

  const notifications = data?.pages.flatMap((page) => page.data) ?? [];
  const hasUnread = notifications.some((item) => item.read_at === null);

  return (
    <div className="min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="space-y-1">
            <h1 className="font-display text-3xl font-semibold tracking-tight">{t("title")}</h1>
            <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => markAll.mutate()}
            disabled={!hasUnread || markAll.isPending}
          >
            <CheckCheck className="mr-2 h-4 w-4" aria-hidden="true" />
            {t("markAllRead")}
          </Button>
        </div>

        <div className="mb-5 inline-flex rounded-lg border bg-muted/40 p-1">
          {(["all", "unread"] as const).map((value) => (
            <Button
              key={value}
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setFilter(value)}
              aria-pressed={filter === value}
              className={cn(
                "h-8 px-3",
                filter === value
                  ? "bg-background text-foreground shadow-sm hover:bg-background"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {t(`filter.${value}`)}
            </Button>
          ))}
        </div>

        {isLoading ? <p className="text-muted-foreground">{tc("loading")}</p> : null}
        {isError ? <p className="text-destructive">{t("loadError")}</p> : null}

        {!isLoading && !isError && notifications.length === 0 ? (
          <div className="animate-fade-up flex flex-col items-center gap-3 rounded-2xl border border-dashed bg-card/40 p-12 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand/10 text-brand">
              <Inbox className="h-6 w-6" aria-hidden="true" />
            </span>
            <p className="text-sm text-muted-foreground">
              {filter === "unread" ? t("emptyUnread") : t("empty")}
            </p>
          </div>
        ) : null}

        {notifications.length > 0 ? (
          <ul className="space-y-3">
            {notifications.map((notification) => (
              <li key={notification.id}>
                <NotificationRow
                  notification={notification}
                  onMarkRead={(id) => markRead.mutate(id)}
                  isMarking={markRead.isPending}
                />
              </li>
            ))}
          </ul>
        ) : null}

        {hasNextPage ? (
          <div className="mt-5 flex justify-center">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchNextPage()}
              disabled={isFetchingNextPage}
            >
              {isFetchingNextPage ? tc("loading") : t("loadMore")}
            </Button>
          </div>
        ) : null}
      </main>
    </div>
  );
}
