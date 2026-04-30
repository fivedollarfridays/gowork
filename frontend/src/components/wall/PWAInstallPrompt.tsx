"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * PWAInstallPrompt — W7 base + polish-2 T41 polish (Driver D).
 *
 * Captures the `beforeinstallprompt` event in browsers that support it
 * (Chromium-based) and surfaces a discreet bottom-LEFT chip with the
 * brand mark + "Install GoWork" + dismiss X. iOS Safari + Firefox never
 * fire the event, so this component is a no-op there.
 *
 * Polish-2 additions:
 *   - 12s auto-hide if the user takes no action (the chip should not
 *     overstay its welcome on a slow viewer).
 *   - Dismissal persists in `localStorage` under `gowork-pwa-dismissed`
 *     for 30 days. While the timestamp is fresh, a fresh
 *     `beforeinstallprompt` event is suppressed (we do NOT pester users
 *     who already said no).
 *
 * Renders nothing on iOS Safari or Firefox (the event never fires).
 */
interface PromptEventLike {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

const STORAGE_KEY = "gowork-pwa-dismissed";
const DISMISS_WINDOW_MS = 30 * 24 * 60 * 60 * 1000; // 30 days
const AUTO_HIDE_MS = 12_000;

function readPromptEvent(e: Event): PromptEventLike | null {
  // Modern Chromium dispatches the BeforeInstallPromptEvent itself.
  const direct = e as Partial<PromptEventLike>;
  if (typeof direct.prompt === "function") {
    return direct as PromptEventLike;
  }
  // Test harness dispatches a CustomEvent with the prompt attached
  // under .detail (see PWAInstallPrompt.test.tsx).
  const custom = (e as CustomEvent<PromptEventLike>).detail;
  if (custom && typeof custom.prompt === "function") return custom;
  return null;
}

/**
 * Returns true when a recent (within 30d) dismissal is recorded. A
 * malformed or missing entry is treated as "not dismissed" (fail-open).
 */
function wasRecentlyDismissed(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return false;
    const parsed = JSON.parse(raw) as { t?: number };
    if (typeof parsed.t !== "number") return false;
    return Date.now() - parsed.t < DISMISS_WINDOW_MS;
  } catch {
    return false;
  }
}

function persistDismissal() {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ t: Date.now() }),
    );
  } catch {
    /* ignore quota errors */
  }
}

function PwaBrandMark(): JSX.Element {
  // Compact monogram for the chip — the full BrandMark component is
  // heavier and lazy-loaded elsewhere; we inline this 16px version so
  // the chip ships zero extra bytes.
  return (
    <svg
      data-pwa-brand
      width={16}
      height={16}
      viewBox="0 0 16 16"
      aria-hidden="true"
      style={{ display: "block" }}
    >
      <rect x={1} y={1} width={14} height={14} rx={3} fill="var(--accent-cyan, #22D3EE)" />
      <path
        d="M4 5h8M4 8h5M4 11h8"
        stroke="var(--bg-base, #0A0E1A)"
        strokeWidth={1.5}
        strokeLinecap="round"
      />
    </svg>
  );
}

export function PWAInstallPrompt(): JSX.Element | null {
  const [evt, setEvt] = useState<PromptEventLike | null>(null);
  const hideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    function onPrompt(e: Event) {
      // Suppress the chip if the user dismissed within 30 days.
      if (wasRecentlyDismissed()) return;
      const handle = readPromptEvent(e);
      if (!handle) return;
      e.preventDefault?.();
      setEvt(handle);
    }
    window.addEventListener("beforeinstallprompt", onPrompt);
    return () => window.removeEventListener("beforeinstallprompt", onPrompt);
  }, []);

  // 12s auto-hide. We start the timer when the chip becomes visible and
  // clear it on unmount or visibility change.
  useEffect(() => {
    if (!evt) return;
    hideTimerRef.current = setTimeout(() => setEvt(null), AUTO_HIDE_MS);
    return () => {
      if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    };
  }, [evt]);

  const onInstall = useCallback(async () => {
    if (!evt) return;
    try {
      await evt.prompt();
      await evt.userChoice;
    } catch {
      /* swallow — native dialog cancelled */
    }
    setEvt(null);
  }, [evt]);

  const onDismiss = useCallback(() => {
    persistDismissal();
    setEvt(null);
  }, []);

  if (!evt) return null;

  return (
    <div
      role="region"
      aria-label="Install GoWork"
      style={{ zIndex: "var(--z-pwa-prompt, 30)" }}
      className="fixed bottom-4 left-4 flex items-center gap-2 rounded-full border border-foreground/15 bg-background/95 px-4 py-2 text-sm shadow-lg backdrop-blur"
    >
      <PwaBrandMark />
      <span className="text-foreground/80">Install GoWork</span>
      <button
        type="button"
        onClick={onInstall}
        className="rounded-full bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground transition hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        Install
      </button>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Dismiss install prompt"
        className="rounded-full px-2 py-1 text-foreground/60 hover:text-foreground"
      >
        {"✕"}
      </button>
    </div>
  );
}
