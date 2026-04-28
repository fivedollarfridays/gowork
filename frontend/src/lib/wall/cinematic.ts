/**
 * First-paint cinematic timing tokens (Spotlight invention).
 *
 * The 4-second TitleSequence is one cinematic. The path-line draw is
 * another. The Mapbox handoff is a third. Without a vocabulary, each
 * surface invents its own ms-literal-and-easing pair, and they drift.
 *
 * This token system declares each step as `{ id, delayMs, durationMs,
 * easing, intent }` so:
 *   - TitleSequence reaches for `getCinematicStep("title").delayMs`
 *   - W2 chapter-intro choreography mirrors the same beats
 *   - Edge states (404, 500) optionally use `handoff` for smooth re-entry
 *
 * If you need a NEW step, add it here — never inline ms literals.
 */

export type CinematicStepId =
  | "presenter"
  | "title"
  | "subtitle"
  | "handoff";

export interface CinematicStep {
  id: CinematicStepId;
  /** Time relative to first paint when the step begins. */
  delayMs: number;
  /** How long the step's animation runs. */
  durationMs: number;
  /** Easing string consumable by both CSS transition + framer-motion. */
  easing: string;
  /** Editorial purpose. Documentation only. */
  intent: string;
}

const EASE_OUT = "cubic-bezier(0.16, 1, 0.3, 1)";

export const CINEMATIC_STEPS: readonly CinematicStep[] = [
  {
    id: "presenter",
    delayMs: 0,
    durationMs: 1000,
    easing: EASE_OUT,
    intent: "GoWork presents — fade in.",
  },
  {
    id: "title",
    delayMs: 1000,
    durationMs: 2000,
    easing: EASE_OUT,
    intent: "The Wall — typewriter in.",
  },
  {
    id: "subtitle",
    delayMs: 3000,
    durationMs: 1000,
    easing: EASE_OUT,
    intent: "An interactive map of Fort Worth — fade in.",
  },
  {
    id: "handoff",
    delayMs: 4000,
    durationMs: 600,
    easing: EASE_OUT,
    intent: "Cinematic resolves; chapter scroll takes over.",
  },
] as const;

export const CINEMATIC_TOTAL_MS = 4600;

const BY_ID = new Map<CinematicStepId, CinematicStep>();
for (const step of CINEMATIC_STEPS) BY_ID.set(step.id, step);

export function getCinematicStep(
  id: CinematicStepId,
): CinematicStep | undefined {
  return BY_ID.get(id);
}
