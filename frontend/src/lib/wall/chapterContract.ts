/**
 * chapterContract — canonical shape for every W2 / W3 chapter component.
 *
 * Driver D Spotlight invention #2.
 *
 * # Why this exists
 *
 * Three parallel drivers shipped chapters in three worktrees. The result:
 *   - Driver A's scaffold accepts {chapterNumber, chapterId, chapterProgress}.
 *   - Driver B's Ch1/Ch2 chapters accept {progress, chapterId}.
 *   - Driver B's Ch3 chapter accepts {progress, active, chapterId}.
 *   - Driver C's Ch4/Ch5 accept {progress, reducedMotion}.
 *
 * Five components, five slightly-different signatures. W3 will ship five
 * more (Ch6-Ch10), and without a contract they'll invent a sixth shape.
 * This module declares the union — every chapter accepts the same props,
 * regardless of which subset it actually uses.
 *
 * # Migration notes
 *
 * - `progress` is LOCAL chapter progress (0..1 within this chapter).
 *   Use `wallProgress.globalToLocal(globalProgress, chapter)` to derive.
 * - `active` is true when the chapter is the "current chapter" — false
 *   when above or below in the scroll. Drives sound triggers + entrance
 *   animations.
 * - `reducedMotion` is OPTIONAL. When omitted, the chapter consults
 *   `usePrefersReducedMotion()` itself.
 * - `chapterId` (slug) and `chapterNumber` (1-indexed) are convenience
 *   props; chapters that don't need them ignore them.
 */

/** Slug used for data attributes + a11y announcements. */
export type ChapterSlug =
  | "continental"
  | "city-arrival"
  | "neighborhood"
  | "wall"
  | "labyrinth"
  | string;

/** Props EVERY chapter component accepts. Some fields are optional so
 *  components only consume what they need. */
export interface ChapterProps {
  /** LOCAL chapter progress 0..1 (within this chapter's scroll range). */
  progress: number;
  /** True when this chapter is the active scroll target. */
  active: boolean;
  /** Optional 1-indexed chapter number (1..10). */
  chapterNumber?: number;
  /** Optional slug used for data-attributes + analytics. */
  chapterId?: ChapterSlug;
  /** Optional reduced-motion override. Chapters consult the hook when omitted. */
  reducedMotion?: boolean;
}

/** Canonical key list — useful for tests + dev-only validators. */
export const CHAPTER_PROP_KEYS = [
  "progress",
  "active",
  "chapterNumber",
  "chapterId",
  "reducedMotion",
] as const;

/** Runtime guard so the dev-tools chapter inspector can validate handoffs. */
export function isChapterProps(value: unknown): value is ChapterProps {
  if (value == null || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  if (typeof v.progress !== "number") return false;
  if (typeof v.active !== "boolean") return false;
  return true;
}

/** Validate a chapter id is in the supported 1..10 range. */
export function isValidChapterId(id: unknown): boolean {
  if (typeof id !== "number") return false;
  if (!Number.isFinite(id)) return false;
  if (!Number.isInteger(id)) return false;
  return id >= 1 && id <= 10;
}
