import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import type { ReactElement } from "react";
import { describe, expect, it } from "vitest";

import { SeverityBadge } from "@/components/severity-badge";
import messages from "@/messages/en.json";

function renderWithIntl(ui: ReactElement) {
  return render(
    <NextIntlClientProvider locale="en" messages={messages}>
      {ui}
    </NextIntlClientProvider>,
  );
}

describe("SeverityBadge", () => {
  it("renders the translated severity label", () => {
    renderWithIntl(<SeverityBadge severity="high" />);
    expect(screen.getByText("High")).toBeInTheDocument();
  });

  it.each([
    ["critical", "Critical", "bg-destructive"],
    ["high", "High", "bg-destructive/15"],
    ["medium", "Medium", "bg-secondary"],
    ["low", "Low", "text-foreground"],
  ])("maps %s to the right badge variant", (severity, label, expectedClass) => {
    renderWithIntl(<SeverityBadge severity={severity} />);
    expect(screen.getByText(label)).toHaveClass(expectedClass);
  });

  it("falls back to the outline variant and raw label for an unknown severity", () => {
    renderWithIntl(<SeverityBadge severity="bogus" />);
    // outline = text-foreground with no bg-* token; unknown severities have no
    // translation key, so the raw value is shown.
    const badge = screen.getByText("bogus");
    expect(badge).toHaveClass("text-foreground");
    expect(badge.className).not.toContain("bg-destructive");
  });
});
