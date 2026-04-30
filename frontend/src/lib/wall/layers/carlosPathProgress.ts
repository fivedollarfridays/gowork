/**
 * Carlos path progress controller (W3 Ch7 — T3.10).
 *
 * The W2 `carlosPath` layer pre-registered a LineString trace with
 * `visibility: none`. W3 Ch7 reveals it AND draws it progressively as
 * Carlos's avatar walks along the path. The math: paint a `line-gradient`
 * with `interpolate` keyed on `line-progress`; the cutoff is where the
 * gradient transitions from opaque-amber to fully-transparent.
 *
 * Idempotency: every method is a no-op when the layer isn't registered
 * (Mapbox style swaps + W2 fallback path are guarded out).
 */

import type { MapboxLikeMap } from "./types";
import { CARLOS_PATH_LINE_ID } from "./carlosPath";

export { CARLOS_PATH_LINE_ID } from "./carlosPath";

import { MAPBOX_COLORS } from "../colors";
const AMBER_STRONG = MAPBOX_COLORS.amberStrong;

function clamp01(v: number): number {
  if (!Number.isFinite(v)) return 0;
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

/** Build a line-gradient expression where the line is opaque up to
 *  `progress` and transparent past it. Uses Mapbox's `line-progress`
 *  feature-state which requires `lineMetrics: true` on the source. */
function buildGradientExpression(progress: number): unknown {
  const p = clamp01(progress);
  // Two stops just above and below the cutoff produce a hard edge — the
  // line "draws" cleanly without a fuzzy fade. p === 1 paints fully
  // opaque amber across the whole line.
  if (p >= 1) {
    return [
      "interpolate",
      ["linear"],
      ["line-progress"],
      0,
      AMBER_STRONG,
      1,
      AMBER_STRONG,
    ];
  }
  if (p <= 0) {
    return [
      "interpolate",
      ["linear"],
      ["line-progress"],
      0,
      "rgba(0,0,0,0)",
      1,
      "rgba(0,0,0,0)",
    ];
  }
  const cutoff = p;
  const slightlyAfter = Math.min(0.999, p + 0.001);
  return [
    "interpolate",
    ["linear"],
    ["line-progress"],
    0,
    AMBER_STRONG,
    cutoff,
    AMBER_STRONG,
    slightlyAfter,
    "rgba(0,0,0,0)",
    1,
    "rgba(0,0,0,0)",
  ];
}

/** Paint the path with a progress-tied gradient. No-op without layer. */
export function setCarlosPathProgress(
  map: MapboxLikeMap,
  progress: number,
): void {
  if (!map.getLayer(CARLOS_PATH_LINE_ID)) return;
  const setPaint = map.setPaintProperty;
  if (!setPaint) return;
  setPaint.call(
    map,
    CARLOS_PATH_LINE_ID,
    "line-gradient",
    buildGradientExpression(progress),
  );
  // Opacity drops to 0 at progress=0 so even a stale gradient never
  // bleeds into Ch6 below.
  setPaint.call(
    map,
    CARLOS_PATH_LINE_ID,
    "line-opacity",
    progress <= 0 ? 0 : 0.95,
  );
}

/** Flip the carlos-path-line layer's visibility. */
export function setCarlosPathVisible(
  map: MapboxLikeMap,
  visible: boolean,
): void {
  if (!map.getLayer(CARLOS_PATH_LINE_ID)) return;
  const setLayout = map.setLayoutProperty;
  if (!setLayout) return;
  setLayout.call(
    map,
    CARLOS_PATH_LINE_ID,
    "visibility",
    visible ? "visible" : "none",
  );
}

/** Restore the W2 hidden state (used on Ch7 unmount). */
export function revertCarlosPath(map: MapboxLikeMap): void {
  setCarlosPathVisible(map, false);
}
