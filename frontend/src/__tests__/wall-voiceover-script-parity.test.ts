/**
 * Spotlight invention #1 (W5 Driver B) — voiceover ↔ chapter copy parity.
 *
 * The submission video script lifts narration from
 * `wall.chapter01..10.hero` (and a few `body` / `subhero` keys). If
 * editorial rewrites the chapter copy, the video script drifts silently
 * — captions and voiceover become wrong without anyone noticing until
 * judges hear the mismatch.
 *
 * This guard test asserts that for each Wall chapter that has a
 * canonical narration anchor (a load-bearing phrase the voiceover
 * lifts), the same phrase appears in `docs/submission-video-script.md`.
 *
 * # Why anchors not full strings
 *
 * Voiceover condenses chapter copy for breath. We don't require
 * verbatim equality — we require a load-bearing phrase to round-trip
 * so the script can't drift to a completely different idea.
 *
 * # If this fires
 *
 * Either editorial copy changed (update the script) or the script was
 * rewritten without re-checking translations. Don't suppress this test
 * — it is the editorial / video sync gate.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const SCRIPT_PATH = join(
  process.cwd(),
  "..",
  "docs",
  "submission-video-script.md",
);
const TRANSLATIONS_PATH = join(
  process.cwd(),
  "src",
  "lib",
  "translations",
  "en.json",
);

interface AnchorSpec {
  chapter: string;
  // The phrase that MUST appear in both the translation and the script.
  // Pulled from each chapter's load-bearing copy line.
  anchor: string;
}

// Canonical anchors per chapter — short, distinctive phrases the voice-
// over has to keep. If editorial rewrites a chapter, update both the
// translation key and this list.
const ANCHORS: AnchorSpec[] = [
  { chapter: "chapter01", anchor: "What's standing between you and a job?" },
  { chapter: "chapter02", anchor: "east of downtown" },
  { chapter: "chapter04", anchor: "barriers don't matter" },
  { chapter: "chapter05", anchor: "Each one says go to the next one" },
  { chapter: "chapter06", anchor: "more pay means less money" },
  // Narrative reset (sprint/narrative-reset, commit 03dff3c) rewrote
  // chapter07 from a 5-week / 5-stop walk to a same-day case file. The
  // load-bearing voiceover anchor is now "twelve weeks" — it appears in
  // the new translation hero ("Don't walk for twelve weeks. Walk in
  // once.") and in the video script's Carlos timeline ("twelve weeks in
  // Fort Worth", "Five stops. Twelve weeks. One plan."). Anchor stays
  // narrow enough to fail on a real drift.
  { chapter: "chapter07", anchor: "twelve weeks" },
  { chapter: "chapter08", anchor: "isn't a list" },
  { chapter: "chapter09", anchor: "It will work where you are" },
  { chapter: "chapter10", anchor: "skip both" },
];

function loadJson(path: string): Record<string, unknown> {
  return JSON.parse(readFileSync(path, "utf8"));
}

function flattenChapter(payload: unknown): string {
  if (typeof payload !== "object" || payload === null) return "";
  return JSON.stringify(payload);
}

describe("Spotlight #1 — voiceover ↔ chapter copy parity", () => {
  const script = readFileSync(SCRIPT_PATH, "utf8");
  const en = loadJson(TRANSLATIONS_PATH);
  const wall = (en.wall ?? {}) as Record<string, unknown>;

  for (const { chapter, anchor } of ANCHORS) {
    it(`${chapter} anchor "${anchor.slice(0, 32)}…" exists in en.json`, () => {
      const flat = flattenChapter(wall[chapter]);
      // Translation may use ASCII or curly apostrophes — collapse before
      // matching so the anchor is robust to copy nits.
      const norm = (s: string) =>
        s.replace(/[''`]/g, "'").replace(/—/g, "—");
      expect(norm(flat).toLowerCase()).toContain(norm(anchor).toLowerCase());
    });

    it(`${chapter} anchor "${anchor.slice(0, 32)}…" appears in video script`, () => {
      // Loosen: case-insensitive substring; punctuation may differ.
      // We also collapse whitespace + strip markdown blockquote markers
      // so anchors that wrap across lines (very common in markdown
      // prose) still resolve as a single substring.
      const norm = (s: string) =>
        s
          .replace(/[''`]/g, "'")
          .replace(/[—–]/g, "-")
          .replace(/^>+\s*/gm, "")
          .replace(/\s+/g, " ")
          .toLowerCase();
      expect(norm(script)).toContain(norm(anchor));
    });
  }
});
