"use client";

import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "@/hooks/useTranslation";

/**
 * T1.53 — Mute toggle.
 *
 * Persists the user's audio preference to localStorage. The default is
 * MUTED (the considerate default for shared spaces, screen-reader
 * users, and surprise auto-play). Once the user opts in, we remember.
 *
 * The button uses `role="switch"` + `aria-checked` so assistive tech
 * announces the state correctly (per ARIA Authoring Practices). The
 * aria-label is sourced from the i18n catalog so EN + ES read it
 * naturally.
 *
 * The on-screen icon is inline SVG (no external icon font); a single
 * speaker-glyph that swaps a slash overlay when muted.
 */
export const MUTE_STORAGE_KEY = "gowork-muted";

function loadInitial(): boolean {
  if (typeof window === "undefined") return true;
  try {
    const v = window.localStorage.getItem(MUTE_STORAGE_KEY);
    if (v === "true") return true;
    if (v === "false") return false;
  } catch {
    /* ignore */
  }
  return true; // default: muted
}

export function MuteToggle(): JSX.Element {
  const { t } = useTranslation();
  const [muted, setMuted] = useState<boolean>(loadInitial);

  useEffect(() => {
    try {
      window.localStorage.setItem(MUTE_STORAGE_KEY, muted ? "true" : "false");
    } catch {
      /* ignore */
    }
  }, [muted]);

  const toggle = useCallback(() => setMuted((m) => !m), []);

  return (
    <button
      type="button"
      role="switch"
      aria-checked={muted}
      aria-label={t("header.muteToggle.aria")}
      onClick={toggle}
      data-mute-toggle
      className="inline-flex h-9 w-9 items-center justify-center rounded-full text-foreground/80 transition hover:bg-foreground/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
    >
      <svg
        viewBox="0 0 24 24"
        width="18"
        height="18"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M11 5L6 9H3v6h3l5 4V5z" />
        {muted ? (
          <line x1="3" y1="3" x2="21" y2="21" stroke="#FB7185" />
        ) : (
          <>
            <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
          </>
        )}
      </svg>
    </button>
  );
}
