import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import type { ReactElement } from "react";
import { describe, expect, it } from "vitest";

import { TierBadge } from "@/components/tier-badge";
import messages from "@/messages/en.json";

function renderWithIntl(ui: ReactElement) {
  return render(
    <NextIntlClientProvider locale="en" messages={messages}>
      {ui}
    </NextIntlClientProvider>,
  );
}

describe("TierBadge", () => {
  it("renders the translated tier label", () => {
    renderWithIntl(<TierBadge tier={1} />);
    expect(screen.getByText("Tier 1")).toBeInTheDocument();
  });

  it.each([
    [1, "bg-primary"],
    [2, "bg-secondary"],
    [3, "text-foreground"],
  ])("emphasis decreases with the tier: tier %s", (tier, expectedClass) => {
    renderWithIntl(<TierBadge tier={tier} />);
    expect(screen.getByText(`Tier ${tier}`)).toHaveClass(expectedClass);
  });

  it("falls back to the outline variant for an out-of-range tier", () => {
    renderWithIntl(<TierBadge tier={9} />);
    const badge = screen.getByText("Tier 9");
    expect(badge).toHaveClass("text-foreground");
    expect(badge.className).not.toContain("bg-primary");
  });
});
