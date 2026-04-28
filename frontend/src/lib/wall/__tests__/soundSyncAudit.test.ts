/**
 * W3 Driver C — T3.25b — Audio sync verification across the spine.
 *
 * For every chapter source file that calls the W1 `play()` sound API,
 * verify:
 *   1. The sound id passed to `play()` is one of the registered
 *      SoundId values (so a typo can't silently make sound never fire).
 *   2. The corresponding asset exists under `public/sounds/`.
 *   3. The chapter file references a reduced-motion path (either by
 *      consulting `usePrefersReducedMotion`, accepting a
 *      `reducedMotion` prop, or wrapping the play call behind such a
 *      check). Defensive: regex-grep, not AST analysis — false-positives
 *      are honestly flagged, not silently suppressed.
 *
 * Defects: dispatch authority forbids modifying other drivers'
 * chapter source. If this test fails for Ch6/Ch7/Ch8/Ch9 (after
 * Drivers A+B merge), souji-sweep + Driver D maximization fixes them.
 */
import { describe, expect, it } from "vitest";
import {
  existsSync,
  readdirSync,
  readFileSync,
  statSync,
} from "node:fs";
import { resolve, join } from "node:path";

const HERE = __dirname;
const FRONTEND_ROOT = resolve(HERE, "../../../../");
const CHAPTERS_DIR = resolve(
  FRONTEND_ROOT,
  "src/components/wall/chapters",
);
const SOUNDS_DIR = resolve(FRONTEND_ROOT, "public/sounds");

// SoundId union from `lib/wall/sound.ts` — kept literal here on
// purpose. If the union changes, this list MUST too (which forces the
// audit author to also update the public/sounds/ assets).
const REGISTERED_SOUND_IDS = [
  "footstep",
  "paper-rustle",
  "calculator-click",
  "chime",
  "wind-ambient",
] as const;

const PLAY_CALL_RE = /play\(\s*["']([a-z-]+)["']/g;

interface ChapterSoundUsage {
  file: string;
  source: string;
  soundIds: ReadonlyArray<string>;
}

function listChapterFiles(): ReadonlyArray<string> {
  if (!existsSync(CHAPTERS_DIR)) return [];
  return readdirSync(CHAPTERS_DIR)
    .filter((n) => /^Chapter\d.*\.tsx$/.test(n))
    .map((n) => join(CHAPTERS_DIR, n));
}

function loadChapterUsage(file: string): ChapterSoundUsage {
  const source = readFileSync(file, "utf-8");
  const soundIds: string[] = [];
  let match: RegExpExecArray | null;
  PLAY_CALL_RE.lastIndex = 0;
  while ((match = PLAY_CALL_RE.exec(source)) !== null) {
    soundIds.push(match[1]);
  }
  return { file, source, soundIds };
}

const USAGE = listChapterFiles().map(loadChapterUsage);
// Only chapters that actually emit a sound are subject to the audit.
const SOUND_EMITTING = USAGE.filter((u) => u.soundIds.length > 0);

describe("T3.25b — every chapter that plays a sound uses a registered SoundId", () => {
  if (SOUND_EMITTING.length === 0) {
    it.skip("no chapter currently emits sound (skipped)", () => {
      // Defensive: when Drivers A+B's chapters land, this skip lifts.
    });
    return;
  }
  it.each(SOUND_EMITTING.map((u) => [u.file, u.soundIds] as const))(
    "%s — every play() id is registered",
    (_file, soundIds) => {
      for (const id of soundIds) {
        expect(REGISTERED_SOUND_IDS as ReadonlyArray<string>).toContain(id);
      }
    },
  );
});

describe("T3.25b — every play()'d sound id has its asset on disk", () => {
  if (SOUND_EMITTING.length === 0) {
    it.skip("no chapter currently emits sound (skipped)", () => undefined);
    return;
  }
  it.each(SOUND_EMITTING.map((u) => [u.file, u.soundIds] as const))(
    "%s — every play() id has a public/sounds/<id>.mp3",
    (_file, soundIds) => {
      for (const id of soundIds) {
        const path = resolve(SOUNDS_DIR, `${id}.mp3`);
        expect(
          existsSync(path),
          `Missing public/sounds/${id}.mp3 (referenced from chapter)`,
        ).toBe(true);
        const stats = statSync(path);
        expect(stats.size).toBeGreaterThan(0);
      }
    },
  );
});

describe("T3.25b — sound-emitting chapters have a reduced-motion path", () => {
  if (SOUND_EMITTING.length === 0) {
    it.skip("no chapter currently emits sound (skipped)", () => undefined);
    return;
  }
  it.each(SOUND_EMITTING.map((u) => [u.file] as const))(
    "%s — references reducedMotion or usePrefersReducedMotion",
    (_file) => {
      const usage = SOUND_EMITTING.find((u) => u.file === _file);
      expect(usage).toBeDefined();
      if (!usage) return;
      const hasReducedMotionRef =
        /reducedMotion|usePrefersReducedMotion/.test(usage.source);
      expect(
        hasReducedMotionRef,
        `Chapter source must reference reducedMotion or usePrefersReducedMotion: ${_file}`,
      ).toBe(true);
    },
  );
});
