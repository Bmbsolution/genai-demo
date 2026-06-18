"use client";

import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { apiFetch, type Data } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { useAuthStore } from "@/lib/store/auth";

type NotificationList = components["schemas"]["NotificationListResponse"];
type UnreadCount = components["schemas"]["UnreadCountResponse"];
type NotificationItem = components["schemas"]["NotificationResponse"];
type MarkAllRead = components["schemas"]["MarkAllReadResponse"];

/** Root query key for everything notification-related, scoped to the signed-in host. */
const notificationsKey = (userId: string | null) => ["notifications", userId] as const;

const PAGE_SIZE = 50;

/**
 * The host's notification list, optionally filtered to unread only. Paginated
 * with offset so an active host can page past the most recent {@link PAGE_SIZE}
 * via `fetchNextPage`; `meta.total` drives whether another page exists.
 */
export function useNotifications({
  unreadOnly = false,
  enabled = true,
}: { unreadOnly?: boolean; enabled?: boolean } = {}) {
  const userId = useAuthStore((state) => state.userId);
  return useInfiniteQuery({
    queryKey: [...notificationsKey(userId), "list", unreadOnly] as const,
    queryFn: ({ pageParam }) =>
      apiFetch<NotificationList>(
        `/api/v1/notifications?unread_only=${unreadOnly}&limit=${PAGE_SIZE}&offset=${pageParam}`,
      ),
    initialPageParam: 0,
    getNextPageParam: (_lastPage, allPages) => {
      const loaded = allPages.reduce((count, page) => count + page.data.length, 0);
      return loaded < allPages[0].meta.total ? loaded : undefined;
    },
    enabled: enabled && Boolean(userId),
  });
}

/**
 * Unread count for the header badge. Polls every 30s and on window focus so the
 * badge stays roughly live without a websocket.
 */
export function useUnreadCount({ enabled = true }: { enabled?: boolean } = {}) {
  const userId = useAuthStore((state) => state.userId);
  return useQuery({
    queryKey: [...notificationsKey(userId), "unread-count"] as const,
    queryFn: () =>
      apiFetch<Data<UnreadCount>>("/api/v1/notifications/unread-count").then(
        (res) => res.data.unread,
      ),
    enabled: enabled && Boolean(userId),
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
  });
}

/** Mark a single notification read; refresh both the list and the badge. */
export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  const userId = useAuthStore((state) => state.userId);
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<Data<NotificationItem>>(`/api/v1/notifications/${id}/read`, {
        method: "PATCH",
      }).then((res) => res.data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: notificationsKey(userId) });
    },
  });
}

/** Mark every unread notification read; refresh both the list and the badge. */
export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();
  const userId = useAuthStore((state) => state.userId);
  return useMutation({
    mutationFn: () =>
      apiFetch<Data<MarkAllRead>>("/api/v1/notifications/read-all", {
        method: "POST",
      }).then((res) => res.data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: notificationsKey(userId) });
    },
  });
}
