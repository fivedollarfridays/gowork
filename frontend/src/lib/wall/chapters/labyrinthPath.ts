/**
 * W2 Driver C — chaotic labyrinth SVG path geometry (T2.42).
 *
 * The labyrinth path traverses 5 offices in a deliberately bad order,
 * loops back, dead-ends, and retraces. It's NOT geo-accurate (Mapbox
 * draws the geo-accurate routes); it's an abstract overlay that says
 * "this is what bureaucracy LOOKS like."
 *
 * We build the path in a normalized 0..1000 viewBox so the consumer can
 * reposition it over whichever map projection is active. Each office
 * lands on a fixed location in this viewBox; the chaotic geometry between
 * them is hand-shaped (not auto-generated) — it's editorial.
 *
 * Spotlight invention #5 — `progressDashoffset(...)`: returns the
 * `stroke-dashoffset` for a given progress 0..1. This lets the caller
 * drive the draw animation off scroll without touching the path string
 * itself. Reduced-motion paths simply pass `1` and get `0` back.
 */

export interface LabyrinthOfficeNode {
  id: string;
  /** Position inside the 0..1000 viewBox. */
  x: number;
  y: number;
}

/** Five normalized office positions. Order is the labyrinth's draw order. */
export const LABYRINTH_NODES: readonly LabyrinthOfficeNode[] = [
  { id: "tarrant-district-clerk", x: 220, y: 380 },
  { id: "hhsc-eligibility", x: 760, y: 480 },
  { id: "trinity-metro-hq", x: 380, y: 620 },
  { id: "legal-aid-nw-texas", x: 580, y: 200 },
  { id: "workforce-solutions-belknap", x: 880, y: 720 },
] as const;

/**
 * The hand-shaped chaotic SVG path. Includes:
 *   - 3 dead-ends (stub branches)
 *   - 2 loops (back-tracks)
 *   - retraced segments
 * Geometry is a single `M ... L ... C ...` string with deliberate
 * inefficiency. Length is approximate (computed below).
 */
export const LABYRINTH_PATH_D: string = [
  "M 220 380",
  "C 320 320, 480 360, 580 200", // off to legal aid
  "L 460 320", // back-track (loop)
  "L 580 200", // retrace dead-end
  "C 700 280, 760 380, 760 480", // forward to HHSC
  "L 660 540", // dead-end branch
  "L 760 480", // retrace
  "C 660 540, 460 580, 380 620", // back to Trinity Metro (loop closes)
  "L 320 700", // dead-end
  "L 380 620", // retrace
  "C 520 660, 720 700, 880 720", // out to Workforce Solutions
  "L 820 600", // dead-end branch
  "L 880 720", // retrace ends at the only "right" node
].join(" ");

/**
 * Approximate total path length used for stroke-dasharray. Hand-tuned to
 * the path above; consumers should treat this as the canonical TOTAL_LENGTH
 * because jsdom's getTotalLength() is unreliable.
 */
export const LABYRINTH_PATH_LENGTH = 2400;

/**
 * Map progress 0..1 to a stroke-dashoffset that draws the path proportionally.
 * progress=0 → fully hidden (offset == length).
 * progress=1 → fully drawn (offset == 0).
 */
export function progressDashoffset(progress: number): number {
  const p = Math.max(0, Math.min(1, progress));
  return Math.round(LABYRINTH_PATH_LENGTH * (1 - p));
}

/**
 * Determine whether a given office node is "lit" at this progress.
 * Offices light up progressively: node 0 lights at the start, node N
 * lights when progress reaches N/totalNodes. The last node lights when
 * progress reaches (count - 1)/count, NOT at progress=1, so the user
 * sees all five lit before the chapter ends.
 */
export function isNodeLit(index: number, progress: number): boolean {
  const p = Math.max(0, Math.min(1, progress));
  const threshold = index / LABYRINTH_NODES.length;
  return p >= threshold;
}
