import { cn } from "@/lib/utils";

/* Decorative confetti — solid dots, no gradients. Overlays a brand cover strip. */
export function Confetti({ className }: { className?: string }) {
  const dots = [
    { x: 8, y: 30, c: "bg-white/70", s: 6 },
    { x: 22, y: 64, c: "bg-white/40", s: 4 },
    { x: 40, y: 20, c: "bg-gold/90", s: 5 },
    { x: 58, y: 56, c: "bg-white/60", s: 7 },
    { x: 74, y: 26, c: "bg-white/40", s: 4 },
    { x: 88, y: 60, c: "bg-gold/80", s: 5 },
  ];
  return (
    <div className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)}>
      {dots.map((d, i) => (
        <span
          key={i}
          className={cn("absolute rounded-full", d.c)}
          style={{ left: `${d.x}%`, top: `${d.y}%`, width: d.s, height: d.s }}
        />
      ))}
    </div>
  );
}
