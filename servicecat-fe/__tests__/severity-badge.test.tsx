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
    ["critical", "Critical", "bg-severity-critical"],
    ["high", "High", "text-severity-high"],
    ["medium", "Medium", "text-severity-medium"],
    ["low", "Low", "text-muted-foreground"],
  ])("maps %s to the right severity token", (severity, label, expectedClass) => {
    renderWithIntl(<SeverityBadge severity={severity} />);
    expect(screen.getByText(label)).toHaveClass(expectedClass);
  });

  it("falls back to the quiet low styling and raw label for an unknown severity", () => {
    renderWithIntl(<SeverityBadge severity="bogus" />);
    // Unknown severities have no translation key, so the raw value is shown,
    // styled like the calm "low" step (muted, no loud fill).
    const badge = screen.getByText("bogus");
    expect(badge).toHaveClass("text-muted-foreground");
    expect(badge.className).not.toContain("bg-severity-critical");
  });
});
