import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";

import { formatRelativeTime } from "@/lib/format-date";

const NOW = new Date("2026-06-18T12:00:00Z");

beforeAll(() => {
  vi.useFakeTimers();
  vi.setSystemTime(NOW);
});

afterAll(() => {
  vi.useRealTimers();
});

describe("formatRelativeTime", () => {
  it("renders a recent past time in minutes", () => {
    const tenMinAgo = new Date(NOW.getTime() - 10 * 60_000).toISOString();
    expect(formatRelativeTime(tenMinAgo)).toBe("10 minutes ago");
  });

  it("renders hours for the same-day past", () => {
    const threeHoursAgo = new Date(NOW.getTime() - 3 * 3_600_000).toISOString();
    expect(formatRelativeTime(threeHoursAgo)).toBe("3 hours ago");
  });

  it("renders days for older timestamps", () => {
    const twoDaysAgo = new Date(NOW.getTime() - 2 * 86_400_000).toISOString();
    expect(formatRelativeTime(twoDaysAgo)).toBe("2 days ago");
  });

  it("renders future timestamps with the 'in' phrasing", () => {
    const inFiveMin = new Date(NOW.getTime() + 5 * 60_000).toISOString();
    expect(formatRelativeTime(inFiveMin)).toBe("in 5 minutes");
  });

  it("falls back to seconds for sub-minute differences", () => {
    const justNow = new Date(NOW.getTime() - 5_000).toISOString();
    expect(formatRelativeTime(justNow)).toBe("5 seconds ago");
  });

  it("reads a timezone-less API timestamp as UTC, not local time", () => {
    // The backend emits naive UTC strings (no Z). 10 minutes before NOW in UTC
    // must read as "10 minutes ago" regardless of the runner's local timezone.
    expect(formatRelativeTime("2026-06-18T11:50:00")).toBe("10 minutes ago");
  });

  it("respects an explicit timezone offset when present", () => {
    // NOW is 12:00Z; 10:00 at +00:00 is two hours earlier.
    expect(formatRelativeTime("2026-06-18T10:00:00+00:00")).toBe("2 hours ago");
  });
});
