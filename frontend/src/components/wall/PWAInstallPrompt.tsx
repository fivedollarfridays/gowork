"use client";

import { useCallback, useEffect, useState } from "react";

/**
 * PWAInstallPrompt — Wave 7 enrichment.
 *
 * Captures the `beforeinstallprompt` event in browsers that support it
 * (Chromium-based). Surfaces a discreet bottom-right affordance with
 * "Install GoWork" and a dismiss control. When the user accepts, the
 * native install dialog runs.
 *
 * Renders nothing on iOS Safari or Firefox (the event never fires).
 */
interface PromptEventLike {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

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

export function PWAInstallPrompt(): JSX.Element | null {
  const [evt, setEvt] = useState<PromptEventLike | null>(null);

  useEffect(() => {
    function onPrompt(e: Event) {
      const handle = readPromptEvent(e);
      if (!handle) return;
      e.preventDefault?.();
      setEvt(handle);
    }
    window.addEventListener("beforeinstallprompt", onPrompt);
    return () => window.removeEventListener("beforeinstallprompt", onPrompt);
  }, []);

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

  const onDismiss = useCallback(() => setEvt(null), []);

  if (!evt) return null;

  return (
    <div
      role="region"
      aria-label="Install GoWork"
      className="fixed bottom-4 right-4 z-[55] flex items-center gap-2 rounded-full border border-foreground/15 bg-background/95 px-4 py-2 text-sm shadow-lg backdrop-blur"
    >
      <span className="text-foreground/80">Install GoWork</span>
      <button
        type="button"
        onClick={onInstall}
        className="rounded-full bg-cyan-400 px-3 py-1 text-xs font-semibold text-slate-900 transition hover:bg-cyan-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
      >
        Install
      </button>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Dismiss install prompt"
        className="rounded-full px-2 py-1 text-foreground/60 hover:text-foreground"
      >
        Dismiss
      </button>
    </div>
  );
}
