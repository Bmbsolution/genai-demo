/**
 * Parse an ISO timestamp from the API. The backend serializes UTC timestamps
 * without a timezone suffix (SQLite drops the tz info), so a tz-less string must
 * be read as UTC — otherwise the browser parses it as local time and every
 * timestamp shifts by the viewer's UTC offset. Strings that already carry a
 * `Z`/offset are left untouched.
 */
function parseApiDate(iso: string): Date {
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(iso);
  return new Date(hasTimezone ? iso : `${iso}Z`);
}

/** Format an ISO timestamp as a friendly event date — client-only (no SSR). */
export function formatEventDate(iso: string): string {
  const date = parseApiDate(iso);
  const day = date.toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  const time = date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  return `${day} · ${time}`;
}

/** A short date (no time) for compact rows. */
export function formatShortDate(iso: string): string {
  return parseApiDate(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

const RELATIVE_UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ["year", 60 * 60 * 24 * 365],
  ["month", 60 * 60 * 24 * 30],
  ["day", 60 * 60 * 24],
  ["hour", 60 * 60],
  ["minute", 60],
];

/** "3 hours ago" / "in 2 days" — localized, client-only (uses the current time). */
export function formatRelativeTime(iso: string): string {
  const seconds = (parseApiDate(iso).getTime() - Date.now()) / 1000;
  const formatter = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });
  for (const [unit, perUnit] of RELATIVE_UNITS) {
    if (Math.abs(seconds) >= perUnit) {
      return formatter.format(Math.round(seconds / perUnit), unit);
    }
  }
  return formatter.format(Math.round(seconds), "second");
}
