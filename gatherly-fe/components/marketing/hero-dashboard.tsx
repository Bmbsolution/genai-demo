"use client";

import { CalendarDays, Check, MapPin, Users } from "lucide-react";
import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";

const GUESTS = [
  { name: "Marie Dubois", initials: "MD", status: "Yes", cls: "bg-success/15 text-success" },
  { name: "Sam Patel", initials: "SP", status: "Maybe", cls: "bg-warning/15 text-warning" },
  { name: "Priya Nair", initials: "PN", status: "Yes", cls: "bg-success/15 text-success" },
];

function Ring({ value }: { value: number }) {
  const r = 22;
  const circ = 2 * Math.PI * r;
  const [shown, setShown] = useState(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setShown(value);
      return;
    }
    const id = window.setTimeout(() => setShown(value), 300);
    return () => window.clearTimeout(id);
  }, [value]);
  return (
    <div className="relative h-14 w-14">
      <svg viewBox="0 0 56 56" className="h-14 w-14 -rotate-90">
        <circle cx="28" cy="28" r={r} fill="none" stroke="hsl(var(--muted))" strokeWidth="6" />
        <circle
          cx="28"
          cy="28"
          r={r}
          fill="none"
          stroke="hsl(var(--brand))"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={circ * (1 - shown / 100)}
          style={{ transition: "stroke-dashoffset 1.3s var(--ease)" }}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-sm font-bold tabular-nums">
        {Math.round(shown)}%
      </span>
    </div>
  );
}

/* The hero centerpiece: a single, comprehensive event dashboard card.
 * Clean corporate styling — soft-square, ambient shadow, hairline border. */
export function HeroDashboard({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "w-full max-w-md overflow-hidden rounded-2xl border border-border/70 bg-card shadow-lift",
        className,
      )}
    >
      <div
        className="relative h-28 bg-brand bg-cover bg-center"
        style={{
          backgroundImage:
            "url(https://images.unsplash.com/photo-1519671482749-fd09be7ccebf?w=900&q=80&auto=format&fit=crop)",
        }}
      >
        <div className="absolute inset-0 bg-navy/45" />
        <span className="absolute left-4 top-4 inline-flex items-center gap-1.5 rounded-md bg-white/15 px-2.5 py-1 text-xs font-semibold text-white backdrop-blur-sm">
          <span className="h-1.5 w-1.5 rounded-full bg-white" /> Published
        </span>
        <span className="absolute right-4 top-4 inline-flex items-center gap-1 rounded-md bg-white/15 px-2.5 py-1 text-xs font-semibold text-white backdrop-blur-sm">
          <Users className="h-3.5 w-3.5" /> 38 / 40
        </span>
      </div>

      <div className="p-6">
        <h3 className="font-corp-display text-xl font-bold tracking-tight text-foreground">
          Summer Rooftop Party
        </h3>
        <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-sm text-muted-foreground">
          <span className="inline-flex items-center gap-2">
            <CalendarDays className="h-4 w-4" /> Sat, Aug 1 · 7:00 PM
          </span>
          <span className="inline-flex items-center gap-2">
            <MapPin className="h-4 w-4" /> The Skyline Loft
          </span>
        </div>

        <div className="mt-5 flex items-center gap-4 rounded-xl border border-border/70 bg-muted/30 p-4">
          <Ring value={78} />
          <div className="flex-1">
            <p className="text-sm font-semibold">Response rate</p>
            <p className="text-xs text-muted-foreground">31 of 40 replied</p>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-md bg-success/15 px-2.5 py-1 text-xs font-semibold text-success">
            <Check className="h-3.5 w-3.5" /> Ready
          </span>
        </div>

        <div className="mt-5 space-y-3 border-t border-border/60 pt-4">
          {GUESTS.map((g) => (
            <div key={g.name} className="flex items-center justify-between">
              <span className="flex items-center gap-2.5">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-muted text-[11px] font-semibold text-muted-foreground">
                  {g.initials}
                </span>
                <span className="text-sm font-medium">{g.name}</span>
              </span>
              <span className={cn("rounded-md px-2.5 py-0.5 text-xs font-semibold", g.cls)}>
                {g.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
