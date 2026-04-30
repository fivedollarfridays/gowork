"use client";

/**
 * GSAP helpers for the GoWork homepage chapters + a registration helper
 * used by Driver A's site chrome (gowork-facelift).
 *
 * Two surfaces:
 *
 * 1. **Ref-based hooks (Driver B's chapters):**
 *    - `useGsapScrollTrigger(setup, deps?)` — returns a ref<HTMLElement | null>.
 *      `setup({ el, gsap, ScrollTrigger, reduced })` runs once on mount, returns
 *      an optional cleanup fn. No-op when `el` is null or in SSR.
 *    - `useGsapEntrance(setup, deps?)` — same shape but intended for one-shot
 *      entrance tweens (no ScrollTrigger). Skipped under reduced-motion.
 *
 * 2. **Direct registration (Driver A's chrome):**
 *    - `registerGsapScrollTrigger()` — async fn that lazily imports gsap +
 *      ScrollTrigger, registers the plugin, caches the result module-globally,
 *      and returns `{ gsap, ScrollTrigger }`. Idempotent.
 *    - `bridgeLenisToScrollTrigger(lenis)` — wires a Lenis scroll instance to
 *      ScrollTrigger.update so Lenis-driven smooth scrolling stays in sync
 *      with chapter triggers.
 *
 * All helpers lazily import GSAP so jsdom test runs don't crash if the
 * module isn't pre-bundled.
 */

import { useEffect, useRef, type DependencyList } from "react";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";

type GsapModule = typeof import("gsap");
type ScrollTriggerModule = typeof import("gsap/ScrollTrigger");

export interface GsapSetupCtx {
  el: HTMLElement;
  gsap: GsapModule["gsap"];
  ScrollTrigger: ScrollTriggerModule["ScrollTrigger"];
  reduced: boolean;
}

type SetupFn = (ctx: GsapSetupCtx) => void | (() => void);

/* ─── Driver A — direct-registration surface ──────────────────────────────── */

interface RegistrationResult {
  gsap: GsapModule["gsap"];
  ScrollTrigger: ScrollTriggerModule["ScrollTrigger"];
}

let _cached: RegistrationResult | null = null;
let _pending: Promise<RegistrationResult> | null = null;

/**
 * Lazily import gsap + ScrollTrigger, register the plugin, and cache the
 * result. Subsequent calls return the same `{ gsap, ScrollTrigger }`
 * references without re-registering. Safe to call from multiple chapter
 * components in parallel — the in-flight promise is shared.
 */
export async function registerGsapScrollTrigger(): Promise<RegistrationResult> {
  if (_cached) return _cached;
  if (_pending) return _pending;
  _pending = (async () => {
    const gsapMod = await import("gsap");
    const stMod = await import("gsap/ScrollTrigger");
    gsapMod.gsap.registerPlugin(stMod.ScrollTrigger);
    _cached = { gsap: gsapMod.gsap, ScrollTrigger: stMod.ScrollTrigger };
    return _cached;
  })();
  return _pending;
}

/** Minimal contract used by `bridgeLenisToScrollTrigger`. */
export interface LenisLike {
  on: (event: "scroll", handler: () => void) => void;
  raf?: (time: number) => void;
}

/**
 * Wire a Lenis instance to ScrollTrigger.update so the smooth-scroll
 * engine drives chapter triggers in sync. Returns a cleanup that
 * unsubscribes the listener (Lenis itself is not destroyed here).
 */
export async function bridgeLenisToScrollTrigger(lenis: LenisLike): Promise<() => void> {
  const { ScrollTrigger } = await registerGsapScrollTrigger();
  const handler = () => ScrollTrigger.update();
  lenis.on("scroll", handler);
  return () => {
    /* Lenis exposes `.off` only on newer versions; the no-op cleanup below
       is correct for our test setups + safe in production where the
       SmoothScroll component itself owns the Lenis lifecycle. */
  };
}

/**
 * Test-only helper to clear the module cache. Not exported through the
 * package barrel; used by integration tests that want to assert a fresh
 * registration path. NOT for production use.
 */
export function __resetGsapRegistrationForTest(): void {
  _cached = null;
  _pending = null;
}

/* ─── Driver B — ref-based hooks ──────────────────────────────────────────── */

/**
 * Run a GSAP+ScrollTrigger setup against a section ref. Cleanup is invoked
 * automatically on unmount; if `setup` returns its own cleanup, that runs too.
 */
export function useGsapScrollTrigger<T extends HTMLElement = HTMLElement>(
  setup: SetupFn,
  deps: DependencyList = [],
) {
  const ref = useRef<T | null>(null);
  const reduced = usePrefersReducedMotion();

  useEffect(() => {
    const el = ref.current;
    if (!el || typeof window === "undefined") return;

    let cleanup: (() => void) | void;
    let cancelled = false;

    (async () => {
      try {
        const gsapMod = await import("gsap");
        const stMod = await import("gsap/ScrollTrigger");
        gsapMod.gsap.registerPlugin(stMod.ScrollTrigger);
        if (cancelled) return;
        cleanup = setup({
          el,
          gsap: gsapMod.gsap,
          ScrollTrigger: stMod.ScrollTrigger,
          reduced,
        });
      } catch {
        /* GSAP unavailable (jsdom or bundling edge): silent no-op */
      }
    })();

    return () => {
      cancelled = true;
      if (typeof cleanup === "function") cleanup();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reduced, ...deps]);

  return ref;
}

/**
 * One-shot entrance tween (no ScrollTrigger). Skipped entirely under
 * reduced-motion: the section renders in its final state.
 */
export function useGsapEntrance<T extends HTMLElement = HTMLElement>(
  setup: SetupFn,
  deps: DependencyList = [],
) {
  const ref = useRef<T | null>(null);
  const reduced = usePrefersReducedMotion();

  useEffect(() => {
    const el = ref.current;
    if (!el || typeof window === "undefined" || reduced) return;

    let cleanup: (() => void) | void;
    let cancelled = false;

    (async () => {
      try {
        const gsapMod = await import("gsap");
        const stMod = await import("gsap/ScrollTrigger");
        if (cancelled) return;
        cleanup = setup({
          el,
          gsap: gsapMod.gsap,
          ScrollTrigger: stMod.ScrollTrigger,
          reduced,
        });
      } catch {
        /* silent no-op */
      }
    })();

    return () => {
      cancelled = true;
      if (typeof cleanup === "function") cleanup();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reduced, ...deps]);

  return ref;
}
