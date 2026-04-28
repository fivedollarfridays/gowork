"use client";

import { useEffect, useRef, useState } from "react";

/**
 * T2.10 — useScrollPin.
 *
 * `position: sticky` is well-supported in modern browsers BUT misbehaves
 * around long scroll containers and overflow ancestors on Safari and
 * older Firefox builds. Chapters in The Wall pin for 10–20% of page
 * scroll length, well into "Safari might unstick" territory.
 *
 * This hook is the JS pinning escape hatch: feature-detects sticky via
 * `CSS.supports`; when unsupported, exposes a `computedTop` consumers can
 * use to pivot to `position: fixed`. When sticky IS supported, the hook
 * is a transparent ref carrier — no behavior change.
 *
 * SSR-safe: defaults to `supportsSticky: true` so initial markup doesn't
 * flash a JS-fixed layout for the majority of users.
 *
 * Spotlight (Structural Lens — Driver A): the brief said "sticky
 * atmosphere via CSS"; the structural failure mode (Safari unstick on
 * long scrolls) becomes a discoverable bug on demo day. Make the
 * fallback explicit, not "we'll see if it works."
 */

export interface ScrollPinState {
  /** Attach to the DOM element that should pin. */
  ref: React.RefObject<HTMLElement | null>;
  /** True while the element is in its pinned range (sticky or JS-fixed). */
  isPinned: boolean;
  /** Top offset (px) the element should occupy when JS-pinned. */
  computedTop: number;
  /** Whether the browser supports `position: sticky`. */
  supportsSticky: boolean;
}

function detectStickySupport(): boolean {
  if (typeof window === "undefined" || typeof window.CSS === "undefined") {
    // SSR / older runtimes — assume sticky works (most users have it).
    return true;
  }
  if (typeof window.CSS.supports !== "function") return true;
  return window.CSS.supports("position", "sticky");
}

/** Hook used by ChapterScaffold to opt into either sticky or JS-pinning. */
export function useScrollPin(): ScrollPinState {
  const ref = useRef<HTMLElement | null>(null);
  const [supportsSticky, setSupportsSticky] = useState<boolean>(true);
  const [isPinned, setIsPinned] = useState<boolean>(false);
  const [computedTop, setComputedTop] = useState<number>(0);

  useEffect(() => {
    setSupportsSticky(detectStickySupport());
  }, []);

  useEffect(() => {
    if (supportsSticky) {
      // Sticky path is a no-op here — the CSS handles pinning, and we
      // expose `isPinned` only when the JS path takes over.
      return;
    }
    const node = ref.current;
    if (!node) return;

    const handleScroll = () => {
      const rect = node.getBoundingClientRect();
      const pinned = rect.top <= 0;
      setIsPinned(pinned);
      setComputedTop(pinned ? 0 : Math.max(0, rect.top));
    };

    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [supportsSticky]);

  return { ref, isPinned, computedTop, supportsSticky };
}
