/**
 * Server-rendered slot wrapper that reserves vertical space for a chapter
 * before its `next/dynamic({ ssr: false })` body has hydrated.
 *
 * Why this exists:
 *   The 8 homepage chapters all use `dynamic(..., { ssr: false })` so SSR
 *   ships <main> with no chapter content at all. On hydration each chapter
 *   mounts in turn and pushes the SiteFooter ~100vh further down the page,
 *   which Lighthouse counts as Cumulative Layout Shift. With 8 chapters
 *   the footer's measured CLS contribution dominates the perf score
 *   (~0.422 of 0.423 total CLS — see lhr from PR #87 CI run on 2026-04-30).
 *
 *   Wrapping each `<ChapterNxxx />` in a server-rendered `<div>` that
 *   carries `min-height: 100vh` reserves the chapter's vertical space at
 *   first paint. The chapter then hydrates INSIDE the slot without
 *   changing the slot's dimensions, so the footer's position is stable
 *   from SSR through hydration.
 *
 * Visual impact: zero in normal use. Hydration completes in <100ms after
 * first paint, well before the user can scroll past the hero. The slot is
 * an empty div (no content, no border, no background) so it is visually
 * invisible behind/above the chapter that hydrates into it. The only
 * edge case is a very slow phone where hydration takes long enough that
 * the user reaches an unhydrated slot — they see a blank section, which
 * is strictly better than today's behavior (popped-up footer, then chapter
 * slams in shoving the footer away).
 *
 * No internal state, no browser-only APIs, no GSAP — pure SSR-safe markup.
 */

import type { ReactNode } from "react";

interface ChapterSlotProps {
  /** The dynamic chapter component (next/dynamic, ssr: false). */
  children: ReactNode;
}

export function ChapterSlot({ children }: ChapterSlotProps): JSX.Element {
  return (
    <div
      data-chapter-slot=""
      style={{
        // 100vh per chapter is the right reservation — every chapter's
        // root <section> uses `min-height: 100vh` (verified across Ch01–Ch08
        // on 2026-04-30). Pinned chapters (Ch04 map +56% scroll, Ch08
        // mic-drop +420% scroll) still own only 100vh of DOM height; the
        // pin holds the section in place visually while scroll continues.
        minHeight: "100vh",
      }}
    >
      {children}
    </div>
  );
}
