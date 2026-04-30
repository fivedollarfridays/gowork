"use client";

import { useEffect } from "react";

/**
 * ChromeAccentBridge — polish-2 T4.
 *
 * Kinetic palette evolution. As each chapter enters the viewport ≥50%,
 * the bridge writes the chapter's signature accent to `--chrome-accent`
 * on `:root`. Header CTA bg + brand-mark glow + header bottom border
 * consume `var(--chrome-accent)` and transition over 800ms.
 *
 * Mapping (locked):
 *   Ch1 = cyan
 *   Ch2 = amber
 *   Ch3 = amber
 *   Ch4 = cyan
 *   Ch5 = amber
 *   Ch6 = status-positive
 *   Ch7 = rose
 *   Ch8 = cyan
 *
 * The component renders nothing — it's a pure side-effect bridge. Mount
 * once near the top of HomePage (Driver E does this immediately after
 * <CursorFlashlight />). Cleans up its IntersectionObserver on unmount
 * so route changes never leak observers.
 */

const ACCENT_BY_CHAPTER: Record<number, string> = {
  1: "var(--accent-cyan)",
  2: "var(--accent-amber)",
  3: "var(--accent-amber)",
  4: "var(--accent-cyan)",
  5: "var(--accent-amber)",
  6: "var(--status-positive)",
  7: "var(--accent-rose)",
  8: "var(--accent-cyan)",
};

const ACTIVATION_RATIO = 0.5;

function chapterIdFromSection(el: Element): number | null {
  const raw = el.id; // expected: chapter-01..chapter-08
  const match = /^chapter-0?(\d+)$/.exec(raw);
  if (!match) return null;
  const n = parseInt(match[1], 10);
  return Number.isFinite(n) && n >= 1 && n <= 8 ? n : null;
}

/** Find the most-visible intersecting chapter section above the activation
 *  threshold. Returns its 1-indexed chapter id, or null. */
function pickActiveChapter(entries: IntersectionObserverEntry[]): number | null {
  let bestRatio = ACTIVATION_RATIO;
  let bestId: number | null = null;
  for (const entry of entries) {
    if (!entry.isIntersecting) continue;
    if (entry.intersectionRatio < ACTIVATION_RATIO) continue;
    const id = chapterIdFromSection(entry.target);
    if (id === null) continue;
    if (entry.intersectionRatio >= bestRatio) {
      bestRatio = entry.intersectionRatio;
      bestId = id;
    }
  }
  return bestId;
}

function collectChapterSections(): Element[] {
  const sections: Element[] = [];
  for (let i = 1; i <= 8; i++) {
    const id = `chapter-${i.toString().padStart(2, "0")}`;
    const el = document.getElementById(id);
    if (el) sections.push(el);
  }
  return sections;
}

export function ChromeAccentBridge(): null {
  useEffect(() => {
    if (typeof window === "undefined" || typeof IntersectionObserver === "undefined") {
      return undefined;
    }
    const sections = collectChapterSections();
    if (sections.length === 0) return undefined;

    const observer = new IntersectionObserver(
      (entries) => {
        const id = pickActiveChapter(entries);
        if (id !== null) {
          const accent = ACCENT_BY_CHAPTER[id];
          if (accent) {
            document.documentElement.style.setProperty("--chrome-accent", accent);
          }
        }
      },
      { threshold: [0.5, 0.75, 1.0] },
    );

    for (const s of sections) observer.observe(s);
    return () => observer.disconnect();
  }, []);

  return null;
}
