import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import type { ReactElement } from "react";
import { describe, expect, it } from "vitest";

import { FindingsTable } from "@/components/findings-table";
import type { components } from "@/lib/api/schema";
import messages from "@/messages/en.json";

type Finding = components["schemas"]["FindingResponse"];

function finding(over: Partial<Finding>): Finding {
  return {
    id: "f1",
    run_id: "r1",
    service_id: "s1",
    criterion_id: "doc.readme_present",
    severity: "high",
    remediation: "Add a README.md",
    evidence: null,
    auto_fixable: true,
    created_at: "2026-05-28T00:00:00Z",
    ...over,
  };
}

function renderWithIntl(ui: ReactElement) {
  return render(
    <NextIntlClientProvider locale="en" messages={messages}>
      {ui}
    </NextIntlClientProvider>,
  );
}

const NAME_BY_ID = new Map([["s1", "payment-svc"]]);

describe("FindingsTable", () => {
  it("renders a row per finding with severity, criterion, and remediation", () => {
    const findings = [
      finding({ id: "f1", criterion_id: "doc.readme_present", remediation: "Add a README.md" }),
      finding({
        id: "f2",
        service_id: "s1",
        criterion_id: "doc.openapi_spec",
        severity: "medium",
        remediation: "Commit an openapi.yaml",
        auto_fixable: false,
      }),
    ];
    renderWithIntl(<FindingsTable findings={findings} nameById={NAME_BY_ID} />);

    expect(screen.getByText("doc.readme_present")).toBeInTheDocument();
    expect(screen.getByText("doc.openapi_spec")).toBeInTheDocument();
    expect(screen.getByText("Add a README.md")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText("Medium")).toBeInTheDocument();
  });

  it("resolves the service name from the map and falls back to the id", () => {
    const findings = [
      finding({ id: "f1", service_id: "s1" }),
      finding({ id: "f2", service_id: "unknown-id" }),
    ];
    renderWithIntl(<FindingsTable findings={findings} nameById={NAME_BY_ID} />);

    expect(screen.getByText("payment-svc")).toBeInTheDocument();
    expect(screen.getByText("unknown-id")).toBeInTheDocument();
  });

  it("shows the auto-fix badge only for auto-fixable findings", () => {
    const findings = [
      finding({ id: "f1", auto_fixable: true }),
      finding({ id: "f2", auto_fixable: false }),
    ];
    renderWithIntl(<FindingsTable findings={findings} nameById={NAME_BY_ID} />);

    expect(screen.getAllByText("Auto-fixable")).toHaveLength(1);
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("hides the Service column when showService is false", () => {
    const findings = [finding({ id: "f1", service_id: "s1" })];
    renderWithIntl(<FindingsTable findings={findings} nameById={NAME_BY_ID} showService={false} />);

    expect(screen.queryByText("Service")).not.toBeInTheDocument();
    expect(screen.queryByText("payment-svc")).not.toBeInTheDocument();
    // The criterion is still shown — only the service column is dropped.
    expect(screen.getByText("doc.readme_present")).toBeInTheDocument();
  });
});
