/**
 * W2 Driver C — Ch4 sub-chapter transition planner (T2.36).
 *
 * Given the previous and next sub-chapter ids, produce a `Ch4TransitionPlan`
 * the WallContainer (Driver A) can apply to the Mapbox instance. The
 * planner is pure — no Mapbox imports — so tests can run in jsdom and so
 * the integration glue stays tiny.
 *
 * The plan has two parts:
 *   - `changes`: a list of office-pin opacity targets (dim the previous,
 *     light the next).
 *   - `creditCheckJobsDimmed`: whether the credit-check-required job
 *     markers should dim to gray (true only inside 4d).
 *
 * Spotlight invention #4 — declarative transition plans: by returning
 * data instead of calling map.setPaintProperty directly, the same plan
 * can be replayed by an SSR snapshot, a Storybook stand-in, or a
 * screenshot test. Driver A keeps the privilege of touching Mapbox; we
 * keep the privilege of describing what changes.
 */
import {
  CH4_SUBCHAPTERS,
  type Ch4SubChapterId,
  getCh4HighlightOffice,
} from "./ch4SubChapter";

/** Soft spring duration; mirrors W1 `--spring-soft` ~ 200ms. */
export const CH4_TRANSITION_DURATION_MS = 200;
/** Reduced-motion duration: instant. */
export const CH4_TRANSITION_DURATION_REDUCED_MS = 0;

export interface OfficeOpacityChange {
  officeId: string;
  targetOpacity: number;
}

export interface Ch4TransitionPlan {
  fromSubChapter: Ch4SubChapterId | null;
  toSubChapter: Ch4SubChapterId;
  durationMs: number;
  changes: OfficeOpacityChange[];
  /** True iff the next sub-chapter is 4d (credit-check job markers dim). */
  creditCheckJobsDimmed: boolean;
}

const HIGHLIGHTED_OPACITY = 1.0;
const DIMMED_OPACITY = 0.4;

export function planCh4Transition(
  from: Ch4SubChapterId | null,
  to: Ch4SubChapterId,
  prefersReducedMotion: boolean,
): Ch4TransitionPlan {
  if (from === to) {
    return {
      fromSubChapter: from,
      toSubChapter: to,
      durationMs: prefersReducedMotion
        ? CH4_TRANSITION_DURATION_REDUCED_MS
        : CH4_TRANSITION_DURATION_MS,
      changes: [],
      creditCheckJobsDimmed: to === "4d",
    };
  }

  const changes: OfficeOpacityChange[] = [];

  if (from) {
    const prevOffice = getCh4HighlightOffice(from);
    if (prevOffice) {
      changes.push({
        officeId: prevOffice.id,
        targetOpacity: DIMMED_OPACITY,
      });
    }
  }

  const nextOffice = getCh4HighlightOffice(to);
  if (nextOffice) {
    changes.push({
      officeId: nextOffice.id,
      targetOpacity: HIGHLIGHTED_OPACITY,
    });
  }

  return {
    fromSubChapter: from,
    toSubChapter: to,
    durationMs: prefersReducedMotion
      ? CH4_TRANSITION_DURATION_REDUCED_MS
      : CH4_TRANSITION_DURATION_MS,
    changes,
    creditCheckJobsDimmed: to === "4d",
  };
}

/** Convenience: the camera bearing offset for a sub-chapter (degrees). */
export function ch4BearingOffset(id: Ch4SubChapterId): number {
  return CH4_SUBCHAPTERS.find((s) => s.id === id)?.bearingOffset ?? 0;
}
