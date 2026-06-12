"use client";

import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/utils";

type RevealVariant = "up" | "left" | "right" | "scale" | "blur";

interface RevealProps {
  children: React.ReactNode;
  className?: string;
  /** Stagger the entrance, in milliseconds. */
  delay?: number;
  /** Entrance direction / effect. Defaults to "up". */
  variant?: RevealVariant;
  /** Render element tag. Defaults to a div. */
  as?: "div" | "section" | "li" | "article";
}

/**
 * Fades + lifts its children into view the first time they enter the viewport.
 * Pure IntersectionObserver — no animation library. Honors prefers-reduced-motion
 * via the `.reveal` CSS (which collapses to a no-op).
 */
export function Reveal({
  children,
  className,
  delay = 0,
  variant = "up",
  as = "div",
}: RevealProps) {
  const ref = useRef<HTMLElement | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node || visible) return;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setVisible(true);
            observer.disconnect();
          }
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -10% 0px" },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [visible]);

  const Tag = as;
  return (
    <Tag
      ref={ref as never}
      className={cn("reveal", `v-${variant}`, visible && "is-visible", className)}
      style={delay ? ({ "--reveal-delay": `${delay}ms` } as React.CSSProperties) : undefined}
    >
      {children}
    </Tag>
  );
}
