"use client";

import { useCallback, useEffect, useState } from "react";

/**
 * Honest cookieless disclosure (Wave 7 enrichment / Spotlight invention).
 *
 * The dispatch's Wisdom lens : do NOT cargo-cult a generic cookie banner
 * for a site that doesn't track. Instead, surface a one-sentence
 * disclosure that says what we actually persist (locale + mute
 * preference in localStorage), with a "Got it" dismissal that we
 * remember.
 *
 * Mounted at the layout root in W2 once Driver A's globals.css ships
 * the fixed-position styles. Until then, the component renders inline.
 */
export const COOKIE_DISCLOSURE_STORAGE_KEY = "gowork-disclosure-dismissed";

function hasDismissed(): boolean {
  if (typeof window === "undefined") return true;
  try {
    return window.localStorage.getItem(COOKIE_DISCLOSURE_STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

export function CookieBanner(): JSX.Element | null {
  const [dismissed, setDismissed] = useState<boolean>(true);

  // Read localStorage on mount (avoid SSR mismatch).
  useEffect(() => {
    setDismissed(hasDismissed());
  }, []);

  const onDismiss = useCallback(() => {
    setDismissed(true);
    try {
      window.localStorage.setItem(COOKIE_DISCLOSURE_STORAGE_KEY, "true");
    } catch {
      /* ignore */
    }
  }, []);

  if (dismissed) return null;

  return (
    <div
      role="region"
      aria-label="Privacy disclosure"
      data-edge-state="disclosure"
      style={{ zIndex: "var(--z-cookie, 30)" }}
      className="fixed bottom-4 left-1/2 -translate-x-1/2 rounded-lg border border-foreground/15 bg-background/95 px-4 py-3 text-sm shadow-lg backdrop-blur sm:max-w-2xl"
    >
      <p className="mb-2 text-foreground/80">
        We do not track. We store your locale and mute preference in
        localStorage so you do not have to set them again.
      </p>
      <button
        type="button"
        onClick={onDismiss}
        className="rounded-full bg-foreground px-3 py-1 text-xs font-semibold text-background transition hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
      >
        Got it
      </button>
    </div>
  );
}
