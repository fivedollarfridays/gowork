"use client";

/**
 * WordReveal — per-word stagger entrance.
 *
 * Splits a string into words and wraps each in a clip-mask + inner span.
 * Words rise from translateY(105%) → 0%, staggered 30ms each. Pairs
 * naturally with MaskReveal: use MaskReveal for whole-line entrances
 * and WordReveal for paragraph-level reveals where the eye should track
 * word-to-word.
 *
 * The emergence is one-shot and reduced-motion is honored.
 */

import { useEffect, useRef, useMemo } from "react";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";

export interface WordRevealProps {
  /** The full string to split + reveal. */
  text: string;
  /** Stagger between words in ms. Default 30. */
  staggerMs?: number;
  /** Initial delay before the first word fires (ms). */
  baseDelayMs?: number;
  /** ms duration per word. Default 900. */
  durationMs?: number;
  /** Threshold for the IntersectionObserver. Default 0.2. */
  threshold?: number;
  /** Optional className passthrough on the outer block. */
  className?: string;
  /** Optional inline style passthrough on the outer block. */
  style?: React.CSSProperties;
  /** rootMargin for the observer. */
  rootMargin?: string;
}

export function WordReveal({
  text,
  staggerMs = 30,
  baseDelayMs = 0,
  durationMs = 900,
  threshold = 0.2,
  className,
  style,
  rootMargin = "0px 0px -10% 0px",
}: WordRevealProps): JSX.Element {
  const ref = useRef<HTMLSpanElement | null>(null);
  const reduced = usePrefersReducedMotion();

  // Split on whitespace but preserve the actual whitespace tokens so the
  // rendered prose keeps its original spacing for clipboard/SEO.
  const tokens = useMemo(() => text.split(/(\s+)/), [text]);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const el = ref.current;
    if (!el) return undefined;
    if (reduced) {
      el.setAttribute("data-revealed", "true");
      return undefined;
    }
    if (typeof IntersectionObserver === "undefined") {
      el.setAttribute("data-revealed", "true");
      return undefined;
    }
    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            (entry.target as HTMLElement).setAttribute("data-revealed", "true");
            io.unobserve(entry.target);
          }
        }
      },
      { threshold, rootMargin },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [reduced, threshold, rootMargin]);

  return (
    <span
      ref={ref}
      data-word-reveal="true"
      data-revealed="false"
      className={className}
      style={style}
    >
      {tokens.map((tok, i) => {
        if (/^\s+$/.test(tok)) {
          return <span key={i}>{tok}</span>;
        }
        const wordIndex = tokens.slice(0, i).filter((t) => !/^\s+$/.test(t)).length;
        const delay = baseDelayMs + wordIndex * staggerMs;
        return (
          <span
            key={i}
            data-word-mask="true"
            style={{
              display: "inline-block",
              overflow: "hidden",
              verticalAlign: "bottom",
              lineHeight: "inherit",
            }}
          >
            <span
              data-word-inner="true"
              style={{
                display: "inline-block",
                transform: "translateY(105%)",
                willChange: "transform",
                transition: `transform ${durationMs}ms cubic-bezier(0.16, 1, 0.3, 1)`,
                transitionDelay: `${delay}ms`,
              }}
            >
              {tok}
            </span>
          </span>
        );
      })}
    </span>
  );
}
