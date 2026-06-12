"use client";

import { CalendarDays, Check, MapPin, PartyPopper, Sparkles, Users } from "lucide-react";

import { Confetti } from "@/components/confetti";
import { cn } from "@/lib/utils";

export { Confetti };

/* SVG progress ring for the "response rate" stat. */
function StatRing({ value, label }: { value: number; label: string }) {
  const r = 26;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - value / 100);
  return (
    <div className="flex items-center gap-3">
      <div className="relative h-16 w-16">
        <svg viewBox="0 0 64 64" className="h-16 w-16 -rotate-90">
          <circle cx="32" cy="32" r={r} fill="none" stroke="hsl(var(--muted))" strokeWidth="7" />
          <circle
            cx="32"
            cy="32"
            r={r}
            fill="none"
            stroke="hsl(var(--brand))"
            strokeWidth="7"
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center font-display text-base font-semibold tabular-nums">
          {value}%
        </span>
      </div>
      <div>
        <p className="text-sm font-semibold">{label}</p>
        <p className="text-xs text-muted-foreground">RSVPs in</p>
      </div>
    </div>
  );
}

const GUESTS = [
  { name: "Marie Dubois", initials: "MD", status: "Yes", cls: "bg-success/15 text-success" },
  { name: "Sam Patel", initials: "SP", status: "Maybe", cls: "bg-warning/15 text-warning" },
  { name: "Priya Nair", initials: "PN", status: "Yes", cls: "bg-success/15 text-success" },
];

/* The hero centerpiece: a polished event card. */
export function EventCardMock({ className }: { className?: string }) {
  return (
    <div className={cn("w-full max-w-sm overflow-hidden surface", className)}>
      <div className="relative h-24 bg-brand">
        <Confetti />
        <span className="absolute left-4 top-4 inline-flex items-center gap-1.5 rounded-full bg-white/15 px-2.5 py-1 text-xs font-semibold text-white backdrop-blur-sm">
          <span className="h-1.5 w-1.5 rounded-full bg-white" /> Published
        </span>
        <span className="absolute right-4 top-4 inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-1 text-xs font-semibold text-white backdrop-blur-sm">
          <Users className="h-3.5 w-3.5" /> 38 / 40
        </span>
      </div>
      <div className="p-5">
        <h3 className="font-display text-xl font-semibold tracking-tight">Summer Rooftop Party</h3>
        <div className="mt-2 space-y-1.5 text-sm text-muted-foreground">
          <p className="inline-flex items-center gap-2">
            <CalendarDays className="h-4 w-4" /> Sat, Aug 1 · 7:00 PM
          </p>
          <p className="inline-flex items-center gap-2">
            <MapPin className="h-4 w-4" /> The Skyline Loft
          </p>
        </div>
        <div className="mt-4 space-y-2.5 border-t border-border/60 pt-4">
          {GUESTS.map((g) => (
            <div key={g.name} className="flex items-center justify-between">
              <span className="flex items-center gap-2.5">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-muted text-[11px] font-semibold text-muted-foreground">
                  {g.initials}
                </span>
                <span className="text-sm font-medium">{g.name}</span>
              </span>
              <span
                className={cn("rounded-full px-2.5 py-0.5 text-xs font-semibold", g.cls)}
              >
                {g.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const READINESS = ["Location set", "Healthy response rate", "Cover image added", "Within capacity"];

/* A floating insights panel — pairs with the hero card. */
export function InsightsMock({ className }: { className?: string }) {
  return (
    <div className={cn("w-64 surface p-4", className)}>
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold">Insights</p>
        <span className="inline-flex items-center gap-1 rounded-full bg-brand/10 px-2 py-0.5 text-[11px] font-semibold text-brand">
          <Sparkles className="h-3 w-3" /> Ready to go
        </span>
      </div>
      <div className="mt-3">
        <StatRing value={78} label="Response rate" />
      </div>
      <ul className="mt-3 space-y-1.5 border-t border-border/60 pt-3">
        {READINESS.map((r) => (
          <li key={r} className="flex items-center gap-2 text-xs text-muted-foreground">
            <Check className="h-3.5 w-3.5 shrink-0 text-success" /> {r}
          </li>
        ))}
      </ul>
    </div>
  );
}

const BOARD = [
  { name: "Marie Dubois", initials: "MD", status: "Yes", cls: "bg-success/15 text-success", in: true },
  { name: "Sam Patel", initials: "SP", status: "Maybe", cls: "bg-warning/15 text-warning", in: false },
  { name: "Jordan Lee", initials: "JL", status: "Yes", cls: "bg-success/15 text-success", in: true },
  { name: "Priya Nair", initials: "PN", status: "Pending", cls: "bg-muted text-muted-foreground", in: false },
];

/* A live guest board — used in the feature bento. */
export function GuestBoardMock({ className }: { className?: string }) {
  return (
    <div className={cn("overflow-hidden rounded-xl border bg-card/60", className)}>
      <div className="flex items-center gap-4 border-b border-border/60 px-4 py-2.5 text-xs">
        <span className="inline-flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-success" />
          <span className="font-semibold tabular-nums">24</span>
          <span className="text-muted-foreground">Yes</span>
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-warning" />
          <span className="font-semibold tabular-nums">6</span>
          <span className="text-muted-foreground">Maybe</span>
        </span>
        <span className="inline-flex items-center gap-1.5 text-muted-foreground">
          <Check className="h-3.5 w-3.5 text-success" /> 12 checked in
        </span>
      </div>
      <div className="divide-y divide-border/50">
        {BOARD.map((g) => (
          <div key={g.name} className="flex items-center justify-between px-4 py-2.5">
            <span className="flex items-center gap-2.5">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-muted text-[11px] font-semibold text-muted-foreground">
                {g.initials}
              </span>
              <span className="text-sm font-medium">{g.name}</span>
            </span>
            <span className="flex items-center gap-2">
              {g.in ? (
                <span className="hidden items-center gap-1 text-[11px] text-success sm:inline-flex">
                  <Check className="h-3 w-3" /> in
                </span>
              ) : null}
              <span className={cn("rounded-full px-2.5 py-0.5 text-xs font-semibold", g.cls)}>
                {g.status}
              </span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* A phone frame showing the guest-facing RSVP page. */
export function RsvpPhoneMock({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "w-56 overflow-hidden rounded-[2rem] border-4 border-foreground/10 bg-card shadow-lift",
        className,
      )}
    >
      <div className="relative h-20 bg-brand">
        <Confetti />
        <span className="absolute left-1/2 top-2 h-1.5 w-12 -translate-x-1/2 rounded-full bg-white/30" />
        <span className="absolute bottom-3 left-4 flex h-9 w-9 items-center justify-center rounded-xl bg-white/15 backdrop-blur-sm">
          <PartyPopper className="h-4 w-4 text-white" />
        </span>
      </div>
      <div className="space-y-3 p-4">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-brand">
            You&apos;re invited
          </p>
          <p className="font-display text-base font-semibold leading-tight">Summer Rooftop Party</p>
        </div>
        <p className="text-xs text-muted-foreground">Hi Jordan, will you come?</p>
        <label className="flex items-center gap-2 text-xs">
          <span className="flex h-4 w-4 items-center justify-center rounded border border-brand bg-brand">
            <Check className="h-3 w-3 text-white" />
          </span>
          I&apos;m bringing a +1
        </label>
        <div className="grid grid-cols-3 gap-1.5">
          <span className="rounded-md bg-brand py-1.5 text-center text-xs font-semibold text-white">
            Yes
          </span>
          <span className="rounded-md border py-1.5 text-center text-xs font-medium text-muted-foreground">
            Maybe
          </span>
          <span className="rounded-md border py-1.5 text-center text-xs font-medium text-muted-foreground">
            No
          </span>
        </div>
      </div>
    </div>
  );
}
