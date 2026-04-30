"use client";

/**
 * TextReveal — premium-Webflow / Lithosquare-style scroll reveal.
 *
 * Wrap any block-level text with `<TextReveal direction="left">` and it
 * fades + slides into place the first time it crosses the viewport. The
 * effect is one-shot (`data-revealed="true"` is sticky once set) so users
 * who scroll back up don't see the transition replay (which feels cheap).
 *
 * Direction grammar:
 *   - "left"  → slides in from the left edge
 *   - "right" → slides in from the right edge
 *   - "up"    → rises from below (default)
 *   - "down"  → drops in from above
 *
 * # Reduced-motion contract
 *
 * `prefers-reduced-motion: reduce` short-circuits the observer so the
 * element renders in its final state on first paint — no opacity/transform
 * dance.
 *
 * # Stagger
 *
 * Wrap multiple TextReveal siblings inside a `[data-reveal-stagger]`
 * container; the CSS rule in `home-velocity.css` cascades a 60ms delay
 * across `:nth-child(N)` so a paragraph block reveals line-by-line.
 *
 * # SSR
 *
 * Renders the children with `data-reveal` + `data-revealed="false"` on
 * SSR. The IntersectionObserver only runs client-side; reduced-motion
 * users + zero-IO browsers see the static state immediately. Either
 * way, the visual contract is "you always see the text" — never a
 * permanently hidden layer if JS doesn't run.
 */

import { useEffect, useRef, type ReactNode } from "react";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";

export type TextRevealDirection = "left" | "right" | "up" | "down";

export interface TextRevealProps {
  children: ReactNode;
  /** Slide-in direction. Default "up". */
  direction?: TextRevealDirection;
  /** Element tag. Default "div" — pass "span" for inline contexts. */
  as?: "div" | "span" | "p" | "li";
  /** Optional className passthrough. */
  className?: string;
  /** Optional inline style passthrough. */
  style?: React.CSSProperties;
  /** Threshold passed to IntersectionObserver. Default 0.18. */
  threshold?: number;
  /** Optional manual delay in ms (overrides nth-child stagger if set). */
  delayMs?: number;
}

export function TextReveal({
  children,
  direction = "up",
  as: As = "div",
  className,
  style,
  threshold = 0.18,
  delayMs,
}: TextRevealProps): JSX.Element {
  const ref = useRef<HTMLElement | null>(null);
  const reduced = usePrefersReducedMotion();

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
      { threshold, rootMargin: "0px 0px -8% 0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [reduced, threshold]);

  // The `as` prop maps to the right JSX intrinsic. Using a small switch
  // keeps the typing strict (no `as any`) and keeps the bundle tiny.
  const props = {
    ref: ref as React.MutableRefObject<HTMLElement | null>,
    "data-reveal": direction,
    "data-revealed": "false",
    className,
    style: delayMs
      ? { ...style, transitionDelay: `${delayMs}ms` }
      : style,
  };

  if (As === "span") {
    return (
      <span
        {...(props as unknown as React.HTMLAttributes<HTMLSpanElement>)}
      >
        {children}
      </span>
    );
  }
  if (As === "p") {
    return (
      <p {...(props as unknown as React.HTMLAttributes<HTMLParagraphElement>)}>
        {children}
      </p>
    );
  }
  if (As === "li") {
    return (
      <li {...(props as unknown as React.HTMLAttributes<HTMLLIElement>)}>
        {children}
      </li>
    );
  }
  return (
    <div {...(props as unknown as React.HTMLAttributes<HTMLDivElement>)}>
      {children}
    </div>
  );
}
