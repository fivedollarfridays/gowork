"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef, type ReactNode } from "react";
import { useReducedMotion } from "framer-motion";

interface ViewTransitionsProviderProps {
  children: ReactNode;
}

interface ViewTransitionDocument {
  startViewTransition?: (cb: () => void) => void;
  __viewTransitionInFlight?: boolean;
}

/**
 * Page-level View Transitions safety net (W1).
 *
 * On every pathname change, fires a one-shot empty
 * `document.startViewTransition` so default Next.js navigations get a
 * subtle cross-fade. SSR-safe and reduced-motion-respecting.
 *
 * # W3 additive extension (T3.21)
 *
 * Callers running their OWN `startViewTransition` (e.g. Chapter 10's
 * "Start your assessment" CTA wrapping `router.push('/assess')` in a
 * cinematic morph) must mark the transition in-flight by setting
 * `document.__viewTransitionInFlight = true` BEFORE the navigation.
 * The provider sees the marker on the next pathname tick, skips its
 * own redundant call, and clears the marker so subsequent navigations
 * resume the default page-level fade.
 *
 * The marker is set automatically by
 * `lib/wall/viewTransitions.startViewTransitionWithFallback` — Driver
 * C's chapter component never touches the marker directly.
 */
export function ViewTransitionsProvider({ children }: ViewTransitionsProviderProps) {
  const pathname = usePathname();
  const prevPathname = useRef(pathname);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    if (pathname === prevPathname.current) return;
    prevPathname.current = pathname;
    if (reducedMotion) return;
    if (typeof document === "undefined") return;
    const doc = document as unknown as ViewTransitionDocument;
    if (doc.__viewTransitionInFlight === true) {
      // Caller (e.g. Ch10 CTA) is already running a transition. Skip
      // the empty page-level one and clear the marker.
      doc.__viewTransitionInFlight = false;
      return;
    }
    if (typeof doc.startViewTransition !== "function") return;
    doc.startViewTransition(() => {});
  }, [pathname, reducedMotion]);

  return <>{children}</>;
}
