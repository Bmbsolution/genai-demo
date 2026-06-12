"use client";

import { Star } from "lucide-react";

import { ThemeToggle } from "@/components/theme-toggle";

/* Premium canvas for the auth screens: ambient halos + dot field, a corner
 * theme toggle, and a centered slot with a trust line. No gradients. */
export function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden p-6">
      <div className="bg-dots pointer-events-none absolute inset-0 [mask-image:radial-gradient(ellipse_60%_50%_at_50%_40%,black,transparent)]" />
      <span className="halo bg-brand/20" style={{ width: 380, height: 380, top: -120, left: -90 }} />
      <span className="halo bg-gold/10" style={{ width: 300, height: 300, bottom: -90, right: -60 }} />

      <div className="absolute right-4 top-4 z-10">
        <ThemeToggle />
      </div>

      <div className="relative z-10 w-full max-w-sm">
        {children}
        <div className="mt-6 flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <span className="inline-flex text-gold">
            {[0, 1, 2, 3, 4].map((s) => (
              <Star key={s} className="h-3 w-3 fill-current" />
            ))}
          </span>
          Loved by 1,200+ hosts
        </div>
      </div>
    </main>
  );
}
