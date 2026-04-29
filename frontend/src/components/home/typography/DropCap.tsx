"use client";

/**
 * Driver C — polish-2 T36 — site-wide drop cap component.
 *
 * Promotes the Ch2-only drop-cap pattern (T15) into a generic component
 * with a per-chapter color override:
 *   - Ch3 → amber
 *   - Ch7 → rose
 *   - Ch8 → amber → cyan gradient
 *
 * Usage:
 *
 *   <DropCap chapter="7">A name on every…</DropCap>
 *
 * Renders an inline `<span>` with the `dropcap` class. The `::first-letter`
 * styling lives in `home-chapters.css` and reads from
 * `--drop-cap-color` (set per chapter via `data-chapter`).
 */

import type { ReactNode, ReactElement } from "react";

export interface DropCapProps {
  /** The chapter the drop-cap belongs to — selects the accent color. */
  chapter: "2" | "3" | "7" | "8";
  /** Optional className to merge with the `dropcap` base class. */
  className?: string;
  /** Inline content (typically a paragraph string). */
  children: ReactNode;
}

export function DropCap({
  chapter,
  className,
  children,
}: DropCapProps): ReactElement {
  const cls = className ? `dropcap ${className}` : "dropcap";
  return (
    <span
      className={cls}
      data-chapter={chapter}
      data-testid={`dropcap-ch${chapter}`}
    >
      {children}
    </span>
  );
}

export default DropCap;
