/* Lightweight line-art illustrations for the "how it works" steps.
 * Brand stroke + muted fills, theme-aware via CSS vars. No external assets. */

const STROKE = "hsl(var(--brand))";
const MUTED = "hsl(var(--muted))";
const FG = "hsl(var(--muted-foreground))";

type Props = { className?: string };

const base = "h-28 w-full";

export function CreateArt({ className = base }: Props) {
  return (
    <svg viewBox="0 0 160 110" fill="none" className={className} aria-hidden="true">
      <rect x="30" y="22" width="100" height="74" rx="10" fill={MUTED} />
      <rect x="30" y="22" width="100" height="74" rx="10" stroke={STROKE} strokeWidth="2.5" />
      <line x1="30" y1="42" x2="130" y2="42" stroke={STROKE} strokeWidth="2.5" />
      <circle cx="48" cy="32" r="3" fill={STROKE} />
      <circle cx="112" cy="32" r="3" fill={STROKE} />
      <line x1="48" y1="16" x2="48" y2="32" stroke={STROKE} strokeWidth="2.5" strokeLinecap="round" />
      <line x1="112" y1="16" x2="112" y2="32" stroke={STROKE} strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="80" cy="69" r="15" fill="hsl(var(--card))" stroke={STROKE} strokeWidth="2.5" />
      <line x1="80" y1="62" x2="80" y2="76" stroke={STROKE} strokeWidth="2.5" strokeLinecap="round" />
      <line x1="73" y1="69" x2="87" y2="69" stroke={STROKE} strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

export function ShareArt({ className = base }: Props) {
  return (
    <svg viewBox="0 0 160 110" fill="none" className={className} aria-hidden="true">
      <rect x="26" y="30" width="78" height="58" rx="10" fill={MUTED} />
      <rect x="26" y="30" width="78" height="58" rx="10" stroke={STROKE} strokeWidth="2.5" />
      <line x1="38" y1="46" x2="76" y2="46" stroke={FG} strokeWidth="2.5" strokeLinecap="round" />
      <line x1="38" y1="58" x2="92" y2="58" stroke={FG} strokeWidth="2.5" strokeLinecap="round" opacity="0.6" />
      <line x1="38" y1="70" x2="66" y2="70" stroke={FG} strokeWidth="2.5" strokeLinecap="round" opacity="0.6" />
      <path d="M104 70 L138 50" stroke={STROKE} strokeWidth="2.5" strokeLinecap="round" />
      <path d="M118 44 L140 48 L132 68 Z" fill="hsl(var(--card))" stroke={STROKE} strokeWidth="2.5" strokeLinejoin="round" />
      <circle cx="120" cy="78" r="6" fill={STROKE} />
    </svg>
  );
}

export function TrackArt({ className = base }: Props) {
  return (
    <svg viewBox="0 0 160 110" fill="none" className={className} aria-hidden="true">
      <rect x="26" y="20" width="108" height="78" rx="10" fill={MUTED} />
      <rect x="26" y="20" width="108" height="78" rx="10" stroke={STROKE} strokeWidth="2.5" />
      <rect x="44" y="62" width="14" height="22" rx="3" fill="hsl(var(--card))" stroke={STROKE} strokeWidth="2.5" />
      <rect x="73" y="50" width="14" height="34" rx="3" fill="hsl(var(--card))" stroke={STROKE} strokeWidth="2.5" />
      <rect x="102" y="38" width="14" height="46" rx="3" fill={STROKE} />
      <circle cx="120" cy="32" r="11" fill="hsl(var(--card))" stroke={STROKE} strokeWidth="2.5" />
      <path d="M115 32 L119 36 L126 28" stroke={STROKE} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
