"use client";

/**
 * T2.6 — ChapterScaffold.
 *
 * Reusable wrapper every chapter (1–10) renders inside. Provides the
 * shared concerns so chapter components can stay focused on editorial:
 *   - sticky positioning (chapter pins while camera flies underneath)
 *   - scroll-tied opacity curve (fade in 0–20%, hold 20–80%, fade 80–100%)
 *   - aria-live region for chapter-id announcement (a11y parity)
 *   - reduced-motion path collapses opacity to constant 1 (instant cut)
 *
 * The opacity computation is exported as a pure function so tests can
 * verify the curve without rendering — and so the flyTo orchestrator
 * (T2.9) can read the same shape if it ever needs to overlap fades.
 *
 * Spotlight (Compound Lens — Driver A): the SAME scaffold serves W2 and
 * W3 (chapters 6–10). Get the contract right once.
 */

import type { ReactNode } from "react";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";

/** Pure curve fn — exported for test + flyTo overlap reuse (T2.114). */
export function computeOverlayOpacity(progress: number, reducedMotion: boolean): number {
  if (reducedMotion) return 1;
  const p = Math.max(0, Math.min(1, progress));
  if (p < 0.2) return p / 0.2;
  if (p > 0.8) return Math.max(0, (1 - p) / 0.2);
  return 1;
}

export interface ChapterScaffoldProps {
  /** 1-indexed chapter number (1..10). */
  chapterNumber: number;
  /** Slug used for data attributes + a11y announcements (e.g., "neighborhood"). */
  chapterId: string;
  /** 0..1 progress within this chapter (from useChapterProgress). */
  chapterProgress: number;
  /** Optional class for outer scroll container. */
  className?: string;
  /** Editorial overlay content. */
  children?: ReactNode;
}

/** Sticky chapter scaffold consumed by every chapter component. */
export default function ChapterScaffold({
  chapterNumber,
  chapterId,
  chapterProgress,
  className,
  children,
}: ChapterScaffoldProps) {
  const reducedMotion = usePrefersReducedMotion();
  const opacity = computeOverlayOpacity(chapterProgress, reducedMotion);

  return (
    <section
      data-chapter-id={chapterId}
      data-chapter-number={String(chapterNumber)}
      className={className}
      style={{
        position: "relative",
        minHeight: "100vh",
      }}
    >
      <div
        // T2.10 useScrollPin would back this with a JS-fixed fallback in
        // unsupported browsers; here we use plain sticky for the modern
        // path and chapters that need the JS path opt-in via the hook.
        style={{
          position: "sticky",
          top: 0,
          height: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          pointerEvents: opacity > 0 ? "auto" : "none",
        }}
      >
        <div
          data-chapter-overlay="true"
          style={{ opacity, transition: reducedMotion ? "none" : "opacity 280ms ease-out" }}
        >
          {children}
        </div>
        <div
          aria-live="polite"
          // Visually hidden announcement region — screen-reader parity.
          style={{
            position: "absolute",
            width: 1,
            height: 1,
            margin: -1,
            padding: 0,
            overflow: "hidden",
            clip: "rect(0,0,0,0)",
            whiteSpace: "nowrap",
            border: 0,
          }}
        >
          {`Chapter ${chapterNumber}: ${chapterId}`}
        </div>
      </div>
    </section>
  );
}
