import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
  useUnreadCount,
} from "@/hooks/use-notifications";
import { apiFetch } from "@/lib/api/client";
import { useAuthStore } from "@/lib/store/auth";

vi.mock("@/lib/api/client", () => ({ apiFetch: vi.fn() }));

const mockFetch = vi.mocked(apiFetch);

function wrapper(client: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

function freshClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

beforeEach(() => {
  useAuthStore.setState({ userId: "u1", accessToken: "at", refreshToken: "rt" });
});

afterEach(() => {
  vi.clearAllMocks();
  useAuthStore.getState().clear();
});

describe("useNotifications", () => {
  it("requests the owner's list with the default (all) filter", async () => {
    mockFetch.mockResolvedValue({ data: [], meta: { limit: 50, offset: 0, total: 0 } });
    const { result } = renderHook(() => useNotifications(), { wrapper: wrapper(freshClient()) });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/notifications?unread_only=false&limit=50&offset=0",
    );
  });

  it("passes unread_only=true when filtering to unread", async () => {
    mockFetch.mockResolvedValue({ data: [], meta: { limit: 50, offset: 0, total: 0 } });
    const { result } = renderHook(() => useNotifications({ unreadOnly: true }), {
      wrapper: wrapper(freshClient()),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/notifications?unread_only=true&limit=50&offset=0",
    );
  });

  it("offers another page and advances the offset while more remain", async () => {
    const page = (count: number, total: number) => ({
      data: Array.from({ length: count }, (_, i) => ({ id: `n${i}` })),
      meta: { limit: 50, offset: 0, total },
    });
    mockFetch.mockResolvedValueOnce(page(50, 60)).mockResolvedValueOnce(page(10, 60));
    const { result } = renderHook(() => useNotifications(), { wrapper: wrapper(freshClient()) });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.hasNextPage).toBe(true);

    await result.current.fetchNextPage();

    await waitFor(() => expect(result.current.hasNextPage).toBe(false));
    expect(mockFetch).toHaveBeenLastCalledWith(
      "/api/v1/notifications?unread_only=false&limit=50&offset=50",
    );
  });

  it("stays disabled when there is no signed-in user", () => {
    useAuthStore.getState().clear();
    const { result } = renderHook(() => useNotifications(), { wrapper: wrapper(freshClient()) });
    expect(result.current.fetchStatus).toBe("idle");
    expect(mockFetch).not.toHaveBeenCalled();
  });
});

describe("useUnreadCount", () => {
  it("unwraps the enveloped unread count", async () => {
    mockFetch.mockResolvedValue({ data: { unread: 7 } });
    const { result } = renderHook(() => useUnreadCount(), { wrapper: wrapper(freshClient()) });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockFetch).toHaveBeenCalledWith("/api/v1/notifications/unread-count");
    expect(result.current.data).toBe(7);
  });
});

describe("mark-read mutations", () => {
  it("marks a single notification read and invalidates the cache", async () => {
    mockFetch.mockResolvedValue({ data: { id: "n1", read_at: "2026-06-18T00:00:00Z" } });
    const client = freshClient();
    const invalidate = vi.spyOn(client, "invalidateQueries");
    const { result } = renderHook(() => useMarkNotificationRead(), { wrapper: wrapper(client) });

    await result.current.mutateAsync("n1");

    expect(mockFetch).toHaveBeenCalledWith("/api/v1/notifications/n1/read", { method: "PATCH" });
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["notifications", "u1"] });
  });

  it("marks all notifications read via the read-all endpoint", async () => {
    mockFetch.mockResolvedValue({ data: { marked: 3 } });
    const client = freshClient();
    const invalidate = vi.spyOn(client, "invalidateQueries");
    const { result } = renderHook(() => useMarkAllNotificationsRead(), {
      wrapper: wrapper(client),
    });

    const res = await result.current.mutateAsync();

    expect(res.marked).toBe(3);
    expect(mockFetch).toHaveBeenCalledWith("/api/v1/notifications/read-all", { method: "POST" });
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["notifications", "u1"] });
  });
});
