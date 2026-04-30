"use client";

/**
 * EdgeStateShell — polish-2 T38 / T39 / T40 (Driver D).
 *
 * Shared shell for branded 404, 500, and loading screens. Reuses the Ch1
 * background pattern (grid + dual glow + grain) so edge states don't feel
 * like a different site. Each consumer passes its own eyebrow + headline +
 * body + CTA, and the shell handles atmosphere + reduced-motion fallback.
 *
 * Renders a `main#main` landmark so the root layout's SkipToContent link
 * still has a valid target on edge routes (Next 13's not-found / error
 * segments don't inherit the layout's <main>).
 *
 * Driver D owns the canonical implementation. Atmosphere is supplied by
 * the existing `Chapter01Background` so the wall metaphor carries straight
 * through the failure state.
 */

import type { ReactNode } from "react";
import { Chapter01Background } from "@/components/home/chapters/_internal/Chapter01Background";

export type EdgeStateKind = "404" | "500" | "loading";

export interface EdgeStateShellProps {
  kind: EdgeStateKind;
  /** Small mono-data tag above the headline (e.g. "404", "500", "…"). */
  eyebrow: string;
  /** The morph word / brand headline. */
  headline: ReactNode;
  /** Optional body copy beneath the headline. */
  body?: ReactNode;
  /** Optional CTA element (button or link) — typically retry / go home. */
  cta?: ReactNode;
  /**
   * Accent that drives the eyebrow color. Defaults to "cyan" (the path).
   * Ch5 `rose` reserved for severe-failure (500) so the user reads the
   * tone before they read the words.
   */
  accent?: "cyan" | "amber" | "rose";
}

const ACCENT_COLOR: Record<NonNullable<EdgeStateShellProps["accent"]>, string> = {
  cyan: "var(--accent-cyan, #22D3EE)",
  amber: "var(--accent-amber, #F59E0B)",
  rose: "var(--accent-rose, #FB7185)",
};

export function EdgeStateShell({
  kind,
  eyebrow,
  headline,
  body,
  cta,
  accent = "cyan",
}: EdgeStateShellProps): JSX.Element {
  return (
    <main
      id="main"
      role="main"
      data-edge-state={kind}
      className="relative isolate mx-auto flex min-h-[80vh] w-full max-w-screen-xl flex-col items-center justify-center overflow-hidden px-6 py-20 text-center"
      style={{ background: "var(--bg-base, #0A0E1A)", color: "var(--fg-primary, #F5F3EE)" }}
    >
      {/* Ch1 atmosphere — grid mask + amber + cyan glow + noise. */}
      <Chapter01Background />

      <div className="relative z-10 mx-auto flex max-w-2xl flex-col items-center gap-6">
        <p
          className="font-mono-data text-xs uppercase tracking-[0.18em]"
          style={{ color: ACCENT_COLOR[accent] }}
        >
          {eyebrow}
        </p>
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
          {headline}
        </h1>
        {body ? (
          <div
            className="max-w-md text-base sm:text-lg"
            style={{ color: "var(--fg-secondary, #A4B3C7)" }}
          >
            {body}
          </div>
        ) : null}
        {cta ? <div className="mt-2 flex gap-3">{cta}</div> : null}
      </div>
    </main>
  );
}
