import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import type { ReactElement } from "react";
import { describe, expect, it } from "vitest";

import { RsvpBadge } from "@/components/rsvp-badge";
import messages from "@/messages/en.json";

function renderWithIntl(ui: ReactElement) {
  return render(
    <NextIntlClientProvider locale="en" messages={messages}>
      {ui}
    </NextIntlClientProvider>,
  );
}

describe("RsvpBadge", () => {
  it("renders the translated status label", () => {
    renderWithIntl(<RsvpBadge status="yes" />);
    expect(screen.getByText("Yes")).toBeInTheDocument();
  });

  it.each([
    ["yes", "Yes", "text-success"],
    ["maybe", "Maybe", "text-warning"],
    ["no", "No", "text-destructive"],
    ["pending", "Pending", "text-muted-foreground"],
  ])("maps %s to its status token", (status, label, expectedClass) => {
    renderWithIntl(<RsvpBadge status={status} />);
    expect(screen.getByText(label)).toHaveClass(expectedClass);
  });

  it("falls back to the quiet pending styling and raw label for an unknown status", () => {
    renderWithIntl(<RsvpBadge status="weird" />);
    const badge = screen.getByText("weird");
    expect(badge).toHaveClass("text-muted-foreground");
    expect(badge.className).not.toContain("text-success");
  });
});
