/* Layered duotone illustrations for the marketing page. Theme-aware via CSS
 * vars. Stroke paths tagged `draw-line` draw in, and `pop` fills scale in, once
 * an ancestor `.draw` gains `.is-visible` (see globals.css + <Reveal className="draw">). */

import type { CSSProperties } from "react";

const BRAND = "hsl(var(--brand))";
const CARD = "hsl(var(--card))";
const MUTED = "hsl(var(--muted))";
const FG = "hsl(var(--muted-foreground))";
const GOLD = "hsl(var(--gold))";
const SUCCESS = "hsl(var(--success))";

type Props = { className?: string };
const base = "h-32 w-full";

const d = (draw?: string, pop?: string): CSSProperties =>
  ({
    ...(draw ? { "--draw-delay": draw } : {}),
    ...(pop ? { "--pop-delay": pop } : {}),
  }) as CSSProperties;

/* Step 1 — create your event (calendar + confetti pop). */
export function CreateArt({ className = base }: Props) {
  return (
    <svg viewBox="0 0 200 140" fill="none" className={className} aria-hidden="true">
      {/* calendar */}
      <rect x="52" y="40" width="96" height="76" rx="10" fill={CARD} />
      <rect
        x="52"
        y="40"
        width="96"
        height="76"
        rx="10"
        stroke={BRAND}
        strokeWidth="2.5"
        className="draw-line"
        style={d("0ms")}
      />
      <path d="M52 58 H148" stroke={BRAND} strokeWidth="2.5" className="draw-line" style={d("250ms")} />
      <circle cx="72" cy="40" r="3.2" fill={BRAND} className="pop" style={d(undefined, "150ms")} />
      <circle cx="128" cy="40" r="3.2" fill={BRAND} className="pop" style={d(undefined, "200ms")} />
      <path d="M72 30 V40 M128 30 V40" stroke={BRAND} strokeWidth="2.5" strokeLinecap="round" className="draw-line" style={d("100ms")} />
      {/* day dots + a highlighted day */}
      {[70, 90, 110, 130].map((x, i) => (
        <circle key={`a${x}`} cx={x} cy="74" r="2.4" fill={FG} className="pop" style={d(undefined, `${300 + i * 40}ms`)} />
      ))}
      {[70, 130].map((x, i) => (
        <circle key={`b${x}`} cx={x} cy="92" r="2.4" fill={FG} className="pop" style={d(undefined, `${460 + i * 40}ms`)} />
      ))}
      <rect x="83" y="84" width="16" height="16" rx="4" fill={BRAND} className="pop" style={d(undefined, "520ms")} />
      <rect x="104" y="84" width="16" height="16" rx="4" fill={MUTED} className="pop" style={d(undefined, "560ms")} />
      {/* confetti pop above */}
      <circle cx="100" cy="22" r="3.6" fill={GOLD} className="pop" style={d(undefined, "650ms")} />
      <circle cx="84" cy="30" r="2.6" fill={BRAND} className="pop" style={d(undefined, "700ms")} />
      <circle cx="118" cy="28" r="2.6" fill={SUCCESS} className="pop" style={d(undefined, "740ms")} />
      <path d="M148 96 q14 -2 18 -16" stroke={GOLD} strokeWidth="2.5" strokeLinecap="round" className="draw-line" style={d("600ms")} />
    </svg>
  );
}

/* Step 2 — invite your guests (card + paper plane trail + avatars). */
export function ShareArt({ className = base }: Props) {
  return (
    <svg viewBox="0 0 200 140" fill="none" className={className} aria-hidden="true">
      {/* invite card */}
      <rect x="26" y="42" width="78" height="60" rx="10" fill={CARD} />
      <rect x="26" y="42" width="78" height="60" rx="10" stroke={BRAND} strokeWidth="2.5" className="draw-line" style={d("0ms")} />
      <path d="M38 58 H82" stroke={FG} strokeWidth="2.5" strokeLinecap="round" className="draw-line" style={d("250ms")} />
      <path d="M38 70 H92" stroke={FG} strokeWidth="2.5" strokeLinecap="round" opacity="0.5" className="draw-line" style={d("350ms")} />
      <path d="M38 82 H68" stroke={FG} strokeWidth="2.5" strokeLinecap="round" opacity="0.5" className="draw-line" style={d("430ms")} />
      {/* trail + paper plane */}
      <path d="M104 78 q34 6 50 -28" stroke={BRAND} strokeWidth="2.2" strokeLinecap="round" strokeDasharray="2 7" className="draw-line" style={d("500ms")} />
      <path d="M150 26 L172 32 L160 50 L156 40 Z" fill={CARD} stroke={BRAND} strokeWidth="2.5" strokeLinejoin="round" className="draw-line" style={d("760ms")} />
      <path d="M156 40 L172 32" stroke={BRAND} strokeWidth="2.5" strokeLinecap="round" className="draw-line" style={d("900ms")} />
      {/* avatars receiving */}
      <circle cx="120" cy="104" r="10" fill={MUTED} stroke={BRAND} strokeWidth="2.5" className="pop" style={d(undefined, "700ms")} />
      <circle cx="142" cy="104" r="10" fill={MUTED} stroke={GOLD} strokeWidth="2.5" className="pop" style={d(undefined, "780ms")} />
      <circle cx="164" cy="104" r="10" fill={BRAND} className="pop" style={d(undefined, "860ms")} />
    </svg>
  );
}

/* Step 3 — watch the RSVPs roll in (dashboard: donut + bars + check). */
export function TrackArt({ className = base }: Props) {
  return (
    <svg viewBox="0 0 200 140" fill="none" className={className} aria-hidden="true">
      <rect x="34" y="30" width="132" height="86" rx="12" fill={CARD} />
      <rect x="34" y="30" width="132" height="86" rx="12" stroke={BRAND} strokeWidth="2.5" className="draw-line" style={d("0ms")} />
      {/* donut */}
      <circle cx="68" cy="73" r="20" stroke={MUTED} strokeWidth="7" />
      <circle
        cx="68"
        cy="73"
        r="20"
        stroke={BRAND}
        strokeWidth="7"
        strokeLinecap="round"
        strokeDasharray="126"
        strokeDashoffset="34"
        className="draw-line"
        style={d("300ms")}
        transform="rotate(-90 68 73)"
      />
      {/* bars */}
      <rect x="108" y="80" width="12" height="20" rx="3" fill={MUTED} className="pop" style={d(undefined, "500ms")} />
      <rect x="126" y="66" width="12" height="34" rx="3" fill={BRAND} opacity="0.55" className="pop" style={d(undefined, "580ms")} />
      <rect x="144" y="54" width="12" height="46" rx="3" fill={BRAND} className="pop" style={d(undefined, "660ms")} />
      {/* check badge */}
      <circle cx="150" cy="38" r="13" fill={SUCCESS} className="pop" style={d(undefined, "820ms")} />
      <path d="M144 38 L148 42 L156 33" stroke={CARD} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" className="draw-line" style={d("1000ms")} />
    </svg>
  );
}

/* Decorative streamers + confetti for the hero — solid filled ribbons (no
 * gradients), fading/scaling in and gently floating. */
export function HeroDecor({ className }: Props) {
  return (
    <svg viewBox="0 0 480 460" fill="none" className={className} aria-hidden="true">
      <path
        d="M20 120 C90 60 150 180 110 250 C80 300 150 340 220 300"
        stroke={BRAND}
        strokeWidth="4"
        strokeLinecap="round"
        opacity="0.18"
        className="animate-float-slow"
      />
      <path
        d="M460 90 C400 130 430 210 380 240 C330 270 380 340 320 380"
        stroke={GOLD}
        strokeWidth="4"
        strokeLinecap="round"
        opacity="0.22"
        className="animate-float"
      />
      <g className="animate-float">
        <rect x="60" y="70" width="12" height="12" rx="3" fill={GOLD} opacity="0.8" transform="rotate(20 66 76)" />
        <circle cx="420" cy="150" r="6" fill={BRAND} opacity="0.5" />
        <circle cx="120" cy="360" r="5" fill={GOLD} opacity="0.7" />
      </g>
      <g className="animate-float-slow">
        <rect x="400" y="330" width="10" height="10" rx="2.5" fill={BRAND} opacity="0.45" transform="rotate(-15 405 335)" />
        <circle cx="70" cy="220" r="4" fill={BRAND} opacity="0.4" />
      </g>
    </svg>
  );
}
