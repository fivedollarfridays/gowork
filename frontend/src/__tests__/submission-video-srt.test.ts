/**
 * T5.B.4 — Submission video SRT captions gate test.
 *
 * Asserts the SRT file:
 *  - Exists at docs/submission-video.srt
 *  - Parses (numbered cues, valid timestamps in HH:MM:SS,mmm format)
 *  - Has at least 12 cues (10 chapters + intro + outro)
 *  - Every cue has non-empty text
 *  - Final cue ends within the 4:30 ceiling
 *  - Timestamps are non-decreasing
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const SRT_PATH = join(process.cwd(), "..", "docs", "submission-video.srt");

interface SrtCue {
  index: number;
  startMs: number;
  endMs: number;
  text: string;
}

const TIMESTAMP_RE = /^(\d{2}):(\d{2}):(\d{2}),(\d{3})$/;

function timestampToMs(stamp: string): number {
  const m = TIMESTAMP_RE.exec(stamp.trim());
  if (!m) throw new Error(`Invalid SRT timestamp: ${stamp}`);
  const [, h, mm, ss, ms] = m;
  return (
    Number(h) * 3_600_000 +
    Number(mm) * 60_000 +
    Number(ss) * 1_000 +
    Number(ms)
  );
}

function parseSrt(raw: string): SrtCue[] {
  const blocks = raw.replace(/\r\n/g, "\n").trim().split(/\n\n+/);
  return blocks.map((block) => {
    const lines = block.split("\n");
    const index = Number.parseInt(lines[0]?.trim() ?? "", 10);
    if (!Number.isFinite(index)) {
      throw new Error(`Invalid SRT index in block: ${block}`);
    }
    const timing = lines[1]?.trim() ?? "";
    const [start, end] = timing.split("-->").map((s) => s.trim());
    if (!start || !end) {
      throw new Error(`Invalid SRT timing in block ${index}: ${timing}`);
    }
    const text = lines.slice(2).join(" ").trim();
    return {
      index,
      startMs: timestampToMs(start),
      endMs: timestampToMs(end),
      text,
    };
  });
}

describe("docs/submission-video.srt", () => {
  const raw = readFileSync(SRT_PATH, "utf8");

  it("exists and is non-empty", () => {
    expect(raw.length).toBeGreaterThan(500);
  });

  it("parses without throwing", () => {
    expect(() => parseSrt(raw)).not.toThrow();
  });

  it("has at least 12 cues (10 chapters + intro + outro)", () => {
    const cues = parseSrt(raw);
    expect(cues.length).toBeGreaterThanOrEqual(12);
  });

  it("uses valid HH:MM:SS,mmm SRT timestamps everywhere", () => {
    const stamps = raw.match(/\d{2}:\d{2}:\d{2},\d{3}/g) ?? [];
    expect(stamps.length).toBeGreaterThanOrEqual(24); // 12 cues × 2 stamps
    for (const s of stamps) {
      expect(s).toMatch(TIMESTAMP_RE);
    }
  });

  it("every cue has non-empty text", () => {
    const cues = parseSrt(raw);
    for (const cue of cues) {
      expect(cue.text.length).toBeGreaterThan(0);
    }
  });

  it("timestamps are non-decreasing across cues", () => {
    const cues = parseSrt(raw);
    let prevEnd = -1;
    for (const cue of cues) {
      expect(cue.startMs).toBeGreaterThanOrEqual(prevEnd);
      expect(cue.endMs).toBeGreaterThan(cue.startMs);
      prevEnd = cue.endMs;
    }
  });

  it("final cue ends within the 4:30 ceiling (270000ms)", () => {
    const cues = parseSrt(raw);
    const last = cues[cues.length - 1];
    expect(last.endMs).toBeLessThanOrEqual(270_000);
  });

  it("cue indices are sequential starting at 1", () => {
    const cues = parseSrt(raw);
    cues.forEach((cue, i) => {
      expect(cue.index).toBe(i + 1);
    });
  });
});
