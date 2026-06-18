import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import type { ReactElement } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import NotificationsPage from "@/app/notifications/page";
import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
} from "@/hooks/use-notifications";
import messages from "@/messages/en.json";

vi.mock("@/components/app-header", () => ({ AppHeader: () => null }));
vi.mock("@/hooks/use-require-auth", () => ({ useRequireAuth: () => ({ ready: true }) }));
vi.mock("@/hooks/use-notifications", () => ({
  useNotifications: vi.fn(),
  useMarkNotificationRead: vi.fn(),
  useMarkAllNotificationsRead: vi.fn(),
}));

const mockList = vi.mocked(useNotifications);
const mockMarkRead = vi.mocked(useMarkNotificationRead);
const mockMarkAll = vi.mocked(useMarkAllNotificationsRead);

type Notification = {
  id: string;
  type: string;
  title: string;
  body: string | null;
  event_id: string | null;
  read_at: string | null;
  created_at: string;
};

function notification(over: Partial<Notification> = {}): Notification {
  return {
    id: "n1",
    type: "guest.rsvp",
    title: "Alex RSVP'd yes",
    body: null,
    event_id: null,
    read_at: null,
    created_at: "2026-06-18T11:00:00Z",
    ...over,
  };
}

function setList(over: Partial<ReturnType<typeof useNotifications>> = {}) {
  mockList.mockReturnValue({
    data: { pages: [], pageParams: [] },
    isLoading: false,
    isError: false,
    hasNextPage: false,
    isFetchingNextPage: false,
    fetchNextPage: vi.fn(),
    ...over,
  } as ReturnType<typeof useNotifications>);
}

const markReadMutate = vi.fn();
const markAllMutate = vi.fn();

function renderPage(ui: ReactElement) {
  return render(
    <NextIntlClientProvider locale="en" messages={messages}>
      {ui}
    </NextIntlClientProvider>,
  );
}

afterEach(() => {
  vi.clearAllMocks();
});

function pagesOf(items: Notification[]) {
  return { pages: [{ data: items, meta: { limit: 50, offset: 0, total: items.length } }] };
}

describe("NotificationsPage", () => {
  it("renders notification titles and enables mark-all when there is unread", () => {
    mockMarkRead.mockReturnValue({ mutate: markReadMutate, isPending: false } as never);
    mockMarkAll.mockReturnValue({ mutate: markAllMutate, isPending: false } as never);
    setList({ data: pagesOf([notification({ title: "Alex RSVP'd yes" })]) as never });

    renderPage(<NotificationsPage />);

    expect(screen.getByText("Alex RSVP'd yes")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mark all read" })).toBeEnabled();
  });

  it("disables mark-all when everything is already read", () => {
    mockMarkRead.mockReturnValue({ mutate: markReadMutate, isPending: false } as never);
    mockMarkAll.mockReturnValue({ mutate: markAllMutate, isPending: false } as never);
    setList({ data: pagesOf([notification({ read_at: "2026-06-18T12:00:00Z" })]) as never });

    renderPage(<NotificationsPage />);

    expect(screen.getByRole("button", { name: "Mark all read" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Mark read" })).not.toBeInTheDocument();
  });

  it("marks a single notification read on click", () => {
    mockMarkRead.mockReturnValue({ mutate: markReadMutate, isPending: false } as never);
    mockMarkAll.mockReturnValue({ mutate: markAllMutate, isPending: false } as never);
    setList({ data: pagesOf([notification({ id: "n42" })]) as never });

    renderPage(<NotificationsPage />);
    fireEvent.click(screen.getByRole("button", { name: "Mark read" }));

    expect(markReadMutate).toHaveBeenCalledWith("n42");
  });

  it("shows the empty state when there are no notifications", () => {
    mockMarkRead.mockReturnValue({ mutate: markReadMutate, isPending: false } as never);
    mockMarkAll.mockReturnValue({ mutate: markAllMutate, isPending: false } as never);
    setList({ data: pagesOf([]) as never });

    renderPage(<NotificationsPage />);

    expect(screen.getByText("You're all caught up — no notifications yet.")).toBeInTheDocument();
  });

  it("shows the error state when the query fails", () => {
    mockMarkRead.mockReturnValue({ mutate: markReadMutate, isPending: false } as never);
    mockMarkAll.mockReturnValue({ mutate: markAllMutate, isPending: false } as never);
    setList({ data: undefined, isError: true });

    renderPage(<NotificationsPage />);

    expect(screen.getByText("Couldn't load your notifications.")).toBeInTheDocument();
  });

  it("switches the active filter when the Unread tab is pressed", () => {
    mockMarkRead.mockReturnValue({ mutate: markReadMutate, isPending: false } as never);
    mockMarkAll.mockReturnValue({ mutate: markAllMutate, isPending: false } as never);
    setList({ data: pagesOf([notification()]) as never });

    renderPage(<NotificationsPage />);
    const unreadTab = screen.getByRole("button", { name: "Unread" });
    fireEvent.click(unreadTab);

    expect(unreadTab).toHaveAttribute("aria-pressed", "true");
  });

  it("renders Load more when another page is available", () => {
    mockMarkRead.mockReturnValue({ mutate: markReadMutate, isPending: false } as never);
    mockMarkAll.mockReturnValue({ mutate: markAllMutate, isPending: false } as never);
    const fetchNextPage = vi.fn();
    setList({ data: pagesOf([notification()]) as never, hasNextPage: true, fetchNextPage });

    renderPage(<NotificationsPage />);
    fireEvent.click(screen.getByRole("button", { name: "Load more" }));

    expect(fetchNextPage).toHaveBeenCalled();
  });
});
