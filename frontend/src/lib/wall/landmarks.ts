/**
 * Landmark map (Spotlight invention).
 *
 * SkipToContent v1 jumps to `#main`. The Wall has more landmarks (header,
 * footer, chapter-list, language-toggle) and a keyboard user should be
 * able to skip to any of them. This module declares the canonical anchor
 * + i18n label map; SkipToContent v2 (W4) consumes it to render a menu.
 *
 * Adding a landmark: append here, add the `a11y.landmarks.*` translation
 * keys to en.json + es.json, and ensure the target element exists.
 */

export type LandmarkId = "main" | "header" | "footer" | "chapters";

export interface Landmark {
  id: LandmarkId;
  /** Hash anchor including leading `#`. */
  anchor: string;
  /** i18n key under a11y.landmarks.<id>. */
  labelKey: string;
}

export const LANDMARKS: readonly Landmark[] = [
  { id: "main", anchor: "#main", labelKey: "a11y.landmarks.main" },
  { id: "header", anchor: "#site-header", labelKey: "a11y.landmarks.header" },
  { id: "footer", anchor: "#site-footer", labelKey: "a11y.landmarks.footer" },
  {
    id: "chapters",
    anchor: "#chapter-list",
    labelKey: "a11y.landmarks.chapters",
  },
] as const;

const BY_ID = new Map<LandmarkId, Landmark>();
for (const lm of LANDMARKS) BY_ID.set(lm.id, lm);

export function getLandmark(id: LandmarkId): Landmark | undefined {
  return BY_ID.get(id);
}
