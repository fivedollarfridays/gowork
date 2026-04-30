"use client";

/**
 * MaskReveal — premium-Webflow line-mask entrance.
 *
 * Wraps a single line of text in a clip-path / overflow-hidden mask and
 * translates the inner content up from translateY(110%) to 0% on first
 * viewport entry. This is the Osmo / Refokus / Locomotive signature
 * move — every premium Webflow scrollytelling site uses some variant.
 *
 * Why not a generic opacity fade-in:
 *   - Mask reveals draw the eye to the type itself, not to opacity changes
 *     which can feel cheap on dense pages.
 *   - The line "rises into existence" rather than "appears" — implies
 *     intention, not random layout.
 *
 * Pair with `WordReveal` for per-word stagger inside a line, or stack
 * MaskReveals via `[data-reveal-stagger]` parent for line-by-line cascade.
 *
 * Reduced-motion: instant final state, no transition.
 */

import { useEffect, useRef, type ReactNode } from "react";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";

export interface MaskRevealProps {
  children: ReactNode;
  /** Tag for the outer mask. Defaults to "span". Use "div" for block lines. */
  as?: "span" | "div" | "h1" | "h2" | "h3" | "p";
  /** Optional className passthrough for the mask wrapper. */
  className?: string;
  /** Style passthrough for the inner translated layer (NOT the mask). */
  innerStyle?: React.CSSProperties;
  /** IntersectionObserver threshold. Defaults to 0.25. */
  threshold?: number;
  /** Manual delay in ms before the inner translates up. */
  delayMs?: number;
  /** rootMargin for the observer (defaults to "0px 0px -10% 0px"). */
  rootMargin?: string;
}

export function MaskReveal({
  children,
  as: As = "span",
  className,
  innerStyle,
  threshold = 0.25,
  delayMs,
  rootMargin = "0px 0px -10% 0px",
}: MaskRevealProps): JSX.Element {
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
      { threshold, rootMargin },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [reduced, threshold, rootMargin]);

  const maskProps = {
    ref: ref as React.MutableRefObject<HTMLElement | null>,
    "data-mask-reveal": "true",
    "data-revealed": "false",
    className,
    style: { display: "inline-block", overflow: "hidden", lineHeight: "inherit" } as React.CSSProperties,
  };

  const innerStyleResolved: React.CSSProperties = {
    display: "inline-block",
    transform: "translateY(110%)",
    willChange: "transform",
    transition: "transform 1100ms cubic-bezier(0.16, 1, 0.3, 1)",
    transitionDelay: delayMs ? `${delayMs}ms` : undefined,
    ...innerStyle,
  };

  const inner = (
    <span data-mask-inner="true" style={innerStyleResolved}>
      {children}
    </span>
  );

  if (As === "div") {
    return (
      <div {...(maskProps as unknown as React.HTMLAttributes<HTMLDivElement>)} style={{ ...maskProps.style, display: "block" }}>
        {inner}
      </div>
    );
  }
  if (As === "h1") {
    return (
      <h1 {...(maskProps as unknown as React.HTMLAttributes<HTMLHeadingElement>)} style={{ ...maskProps.style, display: "block" }}>
        {inner}
      </h1>
    );
  }
  if (As === "h2") {
    return (
      <h2 {...(maskProps as unknown as React.HTMLAttributes<HTMLHeadingElement>)} style={{ ...maskProps.style, display: "block" }}>
        {inner}
      </h2>
    );
  }
  if (As === "h3") {
    return (
      <h3 {...(maskProps as unknown as React.HTMLAttributes<HTMLHeadingElement>)} style={{ ...maskProps.style, display: "block" }}>
        {inner}
      </h3>
    );
  }
  if (As === "p") {
    return (
      <p {...(maskProps as unknown as React.HTMLAttributes<HTMLParagraphElement>)} style={{ ...maskProps.style, display: "block" }}>
        {inner}
      </p>
    );
  }
  return (
    <span {...(maskProps as unknown as React.HTMLAttributes<HTMLSpanElement>)}>
      {inner}
    </span>
  );
}
