"use client";

/**
 * EdgeStateShell — polish-2 T38 / T39 / T40.
 *
 * Shared shell for branded 404, 500, and loading screens. Reuses the Ch1
 * background pattern (grid + dual glow + grain) so edge states don't feel
 * like a different site. Each consumer passes its own eyebrow + headline +
 * CTA, and the shell handles atmosphere + reduced-motion fallback.
 *
 * Driver D owns the canonical implementation.
 */

import type { ReactNode } from "react";

export type EdgeStateKind = "404" | "500" | "loading";

export interface EdgeStateShellProps {
  kind: EdgeStateKind;
  eyebrow: string;
  headline: ReactNode;
  /** Optional body copy beneath the headline. */
  body?: ReactNode;
  /** Optional CTA element (button or link) — typically retry / go home. */
  cta?: ReactNode;
}

export function EdgeStateShell(_props: EdgeStateShellProps): JSX.Element {
  // SCAFFOLD — Driver D fills.
  return (
    <section
      data-edge-state={_props.kind}
      style={{ minHeight: "60vh", padding: "4rem 1.5rem" }}
    >
      <p className="font-mono-data text-xs uppercase tracking-[0.18em]">
        {_props.eyebrow}
      </p>
      <h1 className="text-3xl font-extrabold tracking-tight">
        {_props.headline}
      </h1>
      {_props.body}
      {_props.cta}
    </section>
  );
}
