import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SeverityBadge } from "@/components/severity-badge";

describe("SeverityBadge", () => {
  it("renders the severity label verbatim", () => {
    render(<SeverityBadge severity="high" />);
    expect(screen.getByText("high")).toBeInTheDocument();
  });

  it.each([
    ["critical", "bg-destructive"],
    ["high", "bg-destructive"],
    ["medium", "bg-secondary"],
    ["low", "text-foreground"],
  ])("maps %s to the right badge variant", (severity, expectedClass) => {
    render(<SeverityBadge severity={severity} />);
    expect(screen.getByText(severity)).toHaveClass(expectedClass);
  });

  it("falls back to the outline variant for an unknown severity", () => {
    render(<SeverityBadge severity="bogus" />);
    // outline = text-foreground with no bg-* token.
    const badge = screen.getByText("bogus");
    expect(badge).toHaveClass("text-foreground");
    expect(badge.className).not.toContain("bg-destructive");
  });
});
