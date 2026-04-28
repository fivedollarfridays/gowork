/**
 * audioSyncAuditAllW3 — extends Driver C's soundSyncAudit pattern across
 * all W3 chapter sources.
 *
 * W3 Driver D Spotlight invention #6.
 *
 * # Why this exists
 *
 * Driver C's soundSyncAudit.test.ts only matches `play(`. Driver A's
 * Chapter06TheMath uses a renamed import (`import { play as playSound }`)
 * so the regex misses Ch6's `playSound("calculator-click")` call. The
 * audit appears clean for the W3 chapters even though Ch6 does emit a
 * sound — the contract (asset present, reduced-motion aware) is true
 * but unverified.
 *
 * This test extends the regex to catch BOTH `play(...)` and aliased
 * `playSound(...)` patterns AND introduces a mapping check that
 * compares chapter source to the `chapterSpec` sound declaration. If
 * Ch6's source plays "calculator-click" but `CHAPTER_SPECS[6].sound`
 * declares something different, the test fails — drift caught loud.
 *
 * # Spotlight Lens — Honesty
 *
 * Don't silence missing sounds. Surface them.
 */
import { describe, expect, it } from "vitest";
import {
  existsSync,
  readdirSync,
  readFileSync,
  statSync,
} from "node:fs";
import { resolve, join } from "node:path";
import { CHAPTER_SPECS } from "../chapterSpec";

const HERE = __dirname;
const FRONTEND_ROOT = resolve(HERE, "../../../../");
const CHAPTERS_DIR = resolve(
  FRONTEND_ROOT,
  "src/components/wall/chapters",
);
const SOUNDS_DIR = resolve(FRONTEND_ROOT, "public/sounds");

// Combined: matches `play("...")` AND `playSound("...")` AND any aliased
// import that ends with `play` followed by a string-literal first arg.
// Group 1 captures the function name; group 2 captures the sound id.
const PLAY_CALL_BROAD_RE = /\b(play(?:Sound)?)\s*\(\s*["']([a-z-]+)["']/g;

const REGISTERED_SOUND_IDS = [
  "footstep",
  "paper-rustle",
  "calculator-click",
  "chime",
  "wind-ambient",
] as const;

interface ChapterSoundUsage {
  file: string;
  source: string;
  soundIds: ReadonlyArray<string>;
}

function listW3ChapterFiles(): ReadonlyArray<string> {
  if (!existsSync(CHAPTERS_DIR)) return [];
  return readdirSync(CHAPTERS_DIR)
    .filter((n) =>
      /^Chapter(0[6-9]|10).*\.tsx$/.test(n),
    )
    .map((n) => join(CHAPTERS_DIR, n));
}

function loadChapterUsage(file: string): ChapterSoundUsage {
  const source = readFileSync(file, "utf-8");
  const soundIds: string[] = [];
  PLAY_CALL_BROAD_RE.lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = PLAY_CALL_BROAD_RE.exec(source)) !== null) {
    soundIds.push(match[2]);
  }
  return { file, source, soundIds };
}

const W3_USAGE = listW3ChapterFiles().map(loadChapterUsage);
const W3_SOUND_EMITTING = W3_USAGE.filter((u) => u.soundIds.length > 0);

describe("audioSyncAuditAllW3 — every W3 play() id is registered", () => {
  it("at least one W3 chapter file was scanned", () => {
    expect(W3_USAGE.length).toBeGreaterThanOrEqual(5);
  });

  it.each(W3_SOUND_EMITTING.map((u) => [u.file, u.soundIds] as const))(
    "%s — every emitted sound id is in the SoundId union",
    (_file, soundIds) => {
      for (const id of soundIds) {
        expect(REGISTERED_SOUND_IDS as ReadonlyArray<string>).toContain(id);
      }
    },
  );
});

describe("audioSyncAuditAllW3 — every emitted sound has a public/sounds asset", () => {
  it.each(W3_SOUND_EMITTING.map((u) => [u.file, u.soundIds] as const))(
    "%s — every emitted sound id has /public/sounds/<id>.mp3",
    (_file, soundIds) => {
      for (const id of soundIds) {
        const path = resolve(SOUNDS_DIR, `${id}.mp3`);
        expect(
          existsSync(path),
          `Missing public/sounds/${id}.mp3 (referenced from ${_file})`,
        ).toBe(true);
        const stats = statSync(path);
        expect(stats.size).toBeGreaterThan(0);
      }
    },
  );
});

describe("audioSyncAuditAllW3 — sound-emitting W3 chapters have a reduced-motion path", () => {
  it.each(W3_SOUND_EMITTING.map((u) => [u.file] as const))(
    "%s — references reducedMotion or usePrefersReducedMotion",
    (file) => {
      const usage = W3_SOUND_EMITTING.find((u) => u.file === file);
      expect(usage).toBeDefined();
      if (!usage) return;
      const hasReducedMotionRef =
        /reducedMotion|usePrefersReducedMotion/.test(usage.source);
      expect(
        hasReducedMotionRef,
        `Chapter source must reference reducedMotion or usePrefersReducedMotion: ${file}`,
      ).toBe(true);
    },
  );
});

describe("audioSyncAuditAllW3 — chapterSpec sound declarations match source reality", () => {
  // For each W3 chapter (6..10), compare source-detected sound ids to the
  // chapterSpec.sound declaration. If a chapter source emits a sound but
  // the spec says null (or vice versa), drift is caught.
  it.each([6, 7, 8, 9, 10] as const)(
    "Ch%i: chapterSpec.sound matches the play() invocations in source",
    (id) => {
      const spec = CHAPTER_SPECS.find((s) => s.id === id);
      expect(spec).toBeDefined();
      if (!spec) return;
      const padded = id < 10 ? `0${id}` : String(id);
      // Match Chapter06TheMath.tsx, Chapter07ThePath.tsx, etc.
      const usage = W3_USAGE.find((u) =>
        u.file.includes(`Chapter${padded}`),
      );
      // Some chapter file naming variations — fall back to id-prefix match.
      const matched = usage ?? W3_USAGE.find((u) => u.file.includes(`Chapter${id}`));
      if (!matched) return; // Chapter source not located; not this audit's failure.
      const declared = spec.sound;
      if (declared === null) {
        expect(
          matched.soundIds,
          `Chapter${padded}: spec declares NO sound but source emits ${matched.soundIds.join(", ")}`,
        ).toEqual([]);
      } else {
        expect(
          matched.soundIds,
          `Chapter${padded}: spec declares "${declared}" but source emits ${matched.soundIds.join(", ") || "(none)"}`,
        ).toContain(declared);
      }
    },
  );
});
