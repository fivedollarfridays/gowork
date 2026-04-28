/**
 * chapterSpec — single canonical spec per chapter.
 *
 * W3 Driver D Spotlight invention #1.
 *
 * # Compound Lens
 *
 * Today, eight different surfaces ask "what's the title for chapter 7?",
 * "what camera does Ch4 land on?", "which sound does Ch3 emit?",
 * "what bounds does Ch9 occupy?" — and each surface has to know which
 * module to import. As of W3 close that's:
 *
 *   - chapterCounter (formatCounter / currentChapterFor)
 *   - cameraChoreography (CHAPTER_CAMERAS / TRANSITION_SPEEDS)
 *   - wallProgress (CHAPTER_BOUNDS)
 *   - sound (registered SoundId set)
 *   - i18n translations (wall.chapter0N.*)
 *   - axeChapterRunner (a11y harness)
 *   - wallTimeline (Spotlight #2; chapter ↔ progress lookups)
 *   - dev/wall inspector (Spotlight #4; per-chapter debug rows)
 *
 * Eight modules, eight import statements, eight ways to drift. ChapterSpec
 * is the join key — one record per chapter that aggregates everything.
 *
 * W4 life-layers will need this aggregation FOR EVERY chapter (each layer
 * needs to know "where am I, what camera am I locked to, what sound is
 * playing"). Shipping the spec now means W4 doesn't reinvent it.
 *
 * # Lens — Wisdom
 *
 * The brief asked for "per-chapter context"; the structural answer is
 * "one canonical record, indexed by chapter id."
 */

import type { ChapterId } from "./types";
import { CHAPTER_CAMERAS, type ChapterCameraState } from "./cameraChoreography";
import { CHAPTER_BOUNDS, type ChapterBounds } from "./wallProgress";

/** Stable slug for analytics + dev tools. NOT a translation key. */
export type ChapterSlug =
  | "continental"
  | "city-arrival"
  | "neighborhood"
  | "wall"
  | "labyrinth"
  | "math"
  | "path"
  | "graph"
  | "any-city"
  | "find-your-path";

/** Registered sound ids (mirrors lib/wall/sound.ts). Documented here so
 *  ChapterSpec stays self-describing without circular import to sound.ts. */
export type ChapterSoundId =
  | "footstep"
  | "paper-rustle"
  | "calculator-click"
  | "chime"
  | "wind-ambient"
  | null;

export interface ChapterSpec {
  /** 1-indexed chapter id (1..10). */
  id: ChapterId;
  /** Stable slug used for analytics + dev tools (never translated). */
  slug: ChapterSlug;
  /** Translation key for the chapter's title (resolves in EN + ES). */
  titleKey: string;
  /** Translation key for the chapter's aria-live narration string. */
  ariaKey: string;
  /** Camera state — undefined for chapters not yet wired to Mapbox. */
  camera: ChapterCameraState | undefined;
  /** Global progress bounds (start..end across [0,1]). */
  bounds: ChapterBounds;
  /** Sound id emitted on chapter activation; null if silent. */
  sound: ChapterSoundId;
}

/**
 * Per-chapter sound id. Mirrors the actual `play()` calls in chapter
 * source. Update HERE when a new chapter introduces audio. The
 * audioSyncAuditAllW3 test (Spotlight #6) asserts this matches reality.
 */
const CHAPTER_SOUNDS: Readonly<Record<ChapterId, ChapterSoundId>> = {
  1: null,
  2: null,
  3: "footstep",
  4: null,
  5: "paper-rustle",
  6: "calculator-click",
  7: null,
  8: null,
  9: null,
  10: null,
};

/** Per-chapter slug. Stable — used by analytics + URL fragments. */
const CHAPTER_SLUGS: Readonly<Record<ChapterId, ChapterSlug>> = {
  1: "continental",
  2: "city-arrival",
  3: "neighborhood",
  4: "wall",
  5: "labyrinth",
  6: "math",
  7: "path",
  8: "graph",
  9: "any-city",
  10: "find-your-path",
};

function specFor(id: ChapterId): ChapterSpec {
  const bounds = CHAPTER_BOUNDS[id - 1];
  const camera = (CHAPTER_CAMERAS as Record<number, ChapterCameraState | undefined>)[id];
  const padded = id < 10 ? `0${id}` : String(id);
  return {
    id,
    slug: CHAPTER_SLUGS[id],
    titleKey: `wall.chapter${padded}.title`,
    ariaKey: `wall.chapter${padded}.aria`,
    camera,
    bounds,
    sound: CHAPTER_SOUNDS[id],
  };
}

/** Pre-computed spec for every chapter. Order matches CHAPTER_BOUNDS. */
export const CHAPTER_SPECS: readonly ChapterSpec[] = (
  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const satisfies readonly ChapterId[]
).map(specFor);

/** Look up the spec for a chapter id. Throws on invalid input — the
 *  caller is asking the wrong question. */
export function chapterSpec(id: ChapterId): ChapterSpec {
  const spec = CHAPTER_SPECS.find((s) => s.id === id);
  if (!spec) {
    throw new Error(`chapterSpec: unknown chapter id ${id}`);
  }
  return spec;
}
