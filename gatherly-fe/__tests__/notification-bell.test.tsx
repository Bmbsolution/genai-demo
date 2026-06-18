import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import type { ReactElement } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { NotificationBell } from "@/components/notification-bell";
import { useUnreadCount } from "@/hooks/use-notifications";
import messages from "@/messages/en.json";

vi.mock("next/navigation", () => ({
  usePathname: () => "/events",
}));

vi.mock("@/hooks/use-notifications", () => ({
  useUnreadCount: vi.fn(),
}));

const mockUnread = vi.mocked(useUnreadCount);

function setUnread(value: number | undefined) {
  // Only `data` is read by the component; cast the partial query result.
  mockUnread.mockReturnValue({ data: value } as ReturnType<typeof useUnreadCount>);
}

function renderBell(ui: ReactElement) {
  return render(
    <NextIntlClientProvider locale="en" messages={messages}>
      {ui}
    </NextIntlClientProvider>,
  );
}

afterEach(() => {
  vi.clearAllMocks();
});

describe("NotificationBell", () => {
  it("renders no badge when there are zero unread", () => {
    setUnread(0);
    renderBell(<NotificationBell />);
    expect(screen.queryByText(/\d/)).not.toBeInTheDocument();
    expect(screen.getByRole("link")).toHaveAttribute("aria-label", "Notifications");
  });

  it("treats an undefined (loading) count as zero", () => {
    setUnread(undefined);
    renderBell(<NotificationBell />);
    expect(screen.queryByText(/\d/)).not.toBeInTheDocument();
  });

  it("shows the exact unread count and a pluralized aria-label", () => {
    setUnread(5);
    renderBell(<NotificationBell />);
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByRole("link")).toHaveAttribute(
      "aria-label",
      "Notifications, 5 unread",
    );
  });

  it("caps the badge at 99+ for large counts", () => {
    setUnread(150);
    renderBell(<NotificationBell />);
    expect(screen.getByText("99+")).toBeInTheDocument();
  });

  it("links to the notifications page", () => {
    setUnread(0);
    renderBell(<NotificationBell />);
    expect(screen.getByRole("link")).toHaveAttribute("href", "/notifications");
  });
});
