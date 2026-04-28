/**
 * Spotlight invention #5 (W4 Driver D) — printStylesheet contract.
 *
 * Single source of truth for which CSS selectors are "printable" (a
 * chapter rhythm is preserved when the user prints The Wall) and which
 * are "hidden" (chrome that has no place on a printed page).
 *
 * # Why this exists
 *
 * The print.css file lives in `src/app/styles/print.css`. Without a
 * contract module, drift creeps in: a future driver renames a chapter's
 * `data-chapter-id` and the print pagination silently breaks because
 * print.css still references the old name.
 *
 * This module declares the canonical selector set. The print.css must
 * include every entry. A unit test enforces that.
 *
 * # The companion helper `assertPrintableTree`
 *
 * Walks a DOM root and returns `true` if at least one chapter section is
 * reachable via a printable selector. Used by integration tests that
 * mount the Wall and verify magazine-layout print contract.
 */

/** Selectors that MUST appear in print.css with page-break + keep-together
 *  rules. Any chapter that ships should be reachable via at least one of
 *  these — `assertPrintableTree` enforces that. */
export const PRINTABLE_SECTION_SELECTORS: readonly string[] = [
  ".wall-chapter",
  "section[data-chapter-id]",
];

/** Selectors that MUST appear in print.css with `display: none !important;`.
 *  These represent chrome (header/footer/nav/toggles) and the live Mapbox
 *  canvas — never appropriate on a printed page. */
export const HIDDEN_SELECTORS: readonly string[] = [
  "header",
  "footer",
  "nav",
  ".no-print",
  ".language-toggle",
  ".mute-toggle",
  ".chapter-counter",
  ".mapboxgl-map",
  ".mapbox-container",
];

/**
 * Returns true if the given DOM root contains at least one element that
 * matches a printable section selector. Used by integration tests that
 * mount the Wall and verify the printed magazine layout has anchor
 * points.
 */
export function assertPrintableTree(root: Element): boolean {
  for (const selector of PRINTABLE_SECTION_SELECTORS) {
    if (root.querySelector(selector) !== null) {
      return true;
    }
  }
  return false;
}
