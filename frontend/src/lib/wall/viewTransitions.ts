/**
 * viewTransitions — wall ⇄ assess morph helpers (T3.21).
 *
 * W3 Driver C Spotlight #2.
 *
 * # Why this exists
 *
 * The View Transitions API call site is duplicated three places in W3:
 *   1. Chapter10FindYourPath's "Start your assessment" CTA (dispatch).
 *   2. The contract test that guards the CTA's behavior.
 *   3. The (W4) global ViewTransitionsProvider extension that gates
 *      route-specific morph configs.
 *
 * Three call sites + browser-API + reduced-motion + fallback navigation
 * = a thin module worth its 60 lines. Without it, Firefox users fall
 * through silently because someone forgot to feature-detect.
 *
 * # Browser support (April 2026)
 *
 * - Chrome 111+ : full support (since 2023).
 * - Edge 111+  : full support.
 * - Safari 18  : partial (no cross-document; same-document works).
 * - Firefox    : behind flag at the time of writing — fallback path
 *                MUST be safe (a regular navigation).
 *
 * # CSS contract
 *
 * The matching `view-transition-name: wall-to-assess` is set on:
 *   - Ch10 map snapshot (the Mapbox map div at scroll-end).
 *   - /assess page hero (the form's outer wrapper).
 * Both must use the constant exported here so a typo can't desync them.
 */

/**
 * Canonical CSS view-transition-name shared by Ch10 and /assess. Use
 * this constant in style sheets via a CSS variable or template
 * literal to prevent drift.
 */
export const WALL_TO_ASSESS_TRANSITION_NAME = "wall-to-assess" as const;

/**
 * Feature-detect the View Transitions API. Returns false in SSR + on
 * browsers without `document.startViewTransition` (Firefox).
 */
export function supportsViewTransitions(): boolean {
  if (typeof document === "undefined") return false;
  return typeof (document as unknown as { startViewTransition?: unknown })
    .startViewTransition === "function";
}

/** Options accepted by startViewTransitionWithFallback. */
export interface StartViewTransitionOptions {
  /** When true, skip the API and run a plain navigation (a11y respect). */
  reducedMotion?: boolean;
}

/**
 * Run a navigation callback wrapped in `document.startViewTransition`
 * when the API is available; otherwise just invoke the callback.
 *
 * The callback MUST perform the navigation (router.push, window.location,
 * etc). When the View Transitions API is supported, the browser snapshots
 * the current DOM, runs the callback (which mutates the DOM via the
 * navigation), then animates the morph. When unsupported, the callback
 * runs unwrapped — same end state, no animation.
 */
export function startViewTransitionWithFallback(
  navigate: () => void,
  options: StartViewTransitionOptions = {},
): void {
  if (options.reducedMotion || !supportsViewTransitions()) {
    navigate();
    return;
  }
  const doc = document as unknown as {
    startViewTransition: (cb: () => void) => unknown;
    __viewTransitionInFlight?: boolean;
  };
  // Mark in-flight so the page-level ViewTransitionsProvider skips its
  // redundant empty transition on the next pathname tick. Cleared by
  // the provider once it observes the marker.
  doc.__viewTransitionInFlight = true;
  doc.startViewTransition(() => {
    navigate();
  });
}
