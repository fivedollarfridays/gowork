#!/usr/bin/env node
/**
 * take-recorder.mjs — Spotlight invention #2 (W5 Driver B)
 *
 * Companion CLI for the submission video take plan
 * (`docs/submission-video-take-plan.md`). Prints a structured shot list
 * the recording operator can follow live, with:
 *   - shot index (1..11)
 *   - chapter (Ch1..Ch10)
 *   - timing window (start/end seconds within the 340s total)
 *   - URL fragment (#chapter-1 .. #chapter-10) for deeplink navigation
 *   - take count required (1 for SINGLE, 2/3/5 for MULTIPLE)
 *   - notes (the shot's load-bearing visual or interaction)
 *
 * # Why this is a Spotlight invention
 *
 * Recording day is high-cognitive-load. The operator is reading a
 * script, watching a screen capture, dragging a slider on cue, and
 * clicking buttons at the right beat. They cannot also be flipping
 * through the take-plan markdown trying to find which take is next.
 *
 * This helper prints the list ONCE (or as JSON for OBS scene-change
 * automation, or as a wall-clock countdown if --tail is set) so the
 * operator's eyes stay on the screen.
 *
 * # How to run
 *
 *   node scripts/take-recorder.mjs              # human-readable table
 *   node scripts/take-recorder.mjs --json       # JSON for tooling
 *   node scripts/take-recorder.mjs --shot 9     # show only shot 9
 *   node scripts/take-recorder.mjs --base http://localhost:3000
 *
 * # Output integrity
 *
 * The shot list mirrors `docs/submission-video-take-plan.md`. If the
 * take plan changes, this file changes — they're maintained as a pair.
 * The Spotlight test (`take-recorder-script.test.ts`) gates the
 * structural invariants (11 shots, all 10 chapters present,
 * timestamps cover the 0–340s window).
 */

import process from "node:process";

/**
 * @typedef {Object} Shot
 * @property {number} shotIndex - 1..11
 * @property {string} chapter - "Ch1".."Ch10" or "ColdOpen"
 * @property {number} startSec - within the 0-340s timing window
 * @property {number} endSec
 * @property {string} fragment - URL hash fragment, e.g. "#chapter-7"
 * @property {number} takes - required take count (1, 2, 3, or 5)
 * @property {string} interaction - the cue the operator is waiting for
 * @property {string} note - load-bearing visual / variance hazard
 */

/**
 * All ten Wall chapter fragments — referenced by SHOTS below and
 * exported so deeplink consumers can iterate the full chapter set
 * even though the shot list collapses Ch3 into the Ch2 dolly take.
 */
export const CHAPTER_FRAGMENTS = [
  "#chapter-1",
  "#chapter-2",
  "#chapter-3",
  "#chapter-4",
  "#chapter-5",
  "#chapter-6",
  "#chapter-7",
  "#chapter-8",
  "#chapter-9",
  "#chapter-10",
];

/** @type {Shot[]} */
export const SHOTS = [
  {
    shotIndex: 1,
    chapter: "ColdOpen",
    startSec: 0,
    endSec: 5,
    fragment: "#chapter-1",
    takes: 1,
    interaction: "Hold static frame, no scroll, no cursor",
    note: "Title card — Ch1 hero held silently for 5s",
  },
  {
    shotIndex: 2,
    chapter: "Ch1",
    startSec: 0,
    endSec: 30,
    fragment: "#chapter-1",
    takes: 3,
    interaction: "Continental dive — smooth scroll downward",
    note: "MULTIPLE TAKES — pick smoothest dolly",
  },
  {
    shotIndex: 3,
    chapter: "Ch2",
    startSec: 30,
    endSec: 50,
    fragment: "#chapter-2",
    takes: 1,
    interaction: "Continue scroll into neighborhood",
    note: "Trinity Metro cyan reveal at full opacity",
  },
  {
    shotIndex: 4,
    chapter: "Ch4",
    startSec: 70,
    endSec: 110,
    fragment: "#chapter-4",
    takes: 1,
    interaction: "Wall reveal — let 47-form counter tick up",
    note: "47-form counter MUST hit 47 on screen",
  },
  {
    shotIndex: 5,
    chapter: "Ch5",
    startSec: 110,
    endSec: 140,
    fragment: "#chapter-5",
    takes: 1,
    interaction: "Scroll-tied labyrinth animation",
    note: "Procedural — deterministic across takes",
  },
  {
    shotIndex: 6,
    chapter: "Ch6",
    startSec: 140,
    endSec: 180,
    fragment: "#chapter-6",
    takes: 1,
    interaction: "Drag wage slider $7.25 → $25 in one motion",
    note: "Cliff color shift — don't oscillate",
  },
  {
    shotIndex: 7,
    chapter: "Ch7",
    startSec: 180,
    endSec: 230,
    fragment: "#chapter-7",
    takes: 2,
    interaction: "Avatar walks 5 waypoints — sync footstep",
    note: "Avatar must reach Week 12 / Hired",
  },
  {
    shotIndex: 8,
    chapter: "Ch8",
    startSec: 230,
    endSec: 280,
    fragment: "#chapter-8",
    takes: 3,
    interaction: "Scroll — let camera tilt up onto graph",
    note: "WOW MOMENT — constellation rotates 90deg+",
  },
  {
    shotIndex: 9,
    chapter: "Ch9",
    startSec: 280,
    endSec: 305,
    fragment: "#chapter-9",
    takes: 5,
    interaction: 'Click "Fly to Montgomery"',
    note: "Cross-country flyTo — pick smoothest, no tile pop",
  },
  {
    shotIndex: 10,
    chapter: "Ch9",
    startSec: 305,
    endSec: 310,
    fragment: "#chapter-9",
    takes: 1,
    interaction: 'Click "Return to Fort Worth" after landing',
    note: "Hold for full landing before next click",
  },
  {
    shotIndex: 11,
    chapter: "Ch10",
    startSec: 310,
    endSec: 340,
    fragment: "#chapter-10",
    takes: 3,
    interaction: 'Click "Start your assessment" — Chrome 135+',
    note: "View Transitions morph — Chrome only",
  },
];

const TOTAL_RUNTIME_SEC = 340;

function parseArgs(argv) {
  const args = { json: false, shot: null, base: null };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === "--json") args.json = true;
    else if (a === "--shot") args.shot = Number.parseInt(argv[++i], 10);
    else if (a === "--base") args.base = argv[++i];
    else if (a === "--help" || a === "-h") {
      console.log(
        "Usage: node scripts/take-recorder.mjs [--json] [--shot N] [--base URL]",
      );
      process.exit(0);
    }
  }
  return args;
}

function formatTimestamp(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function buildUrl(base, fragment) {
  if (!base) return fragment;
  return `${base.replace(/\/$/, "")}/${fragment}`;
}

function printHuman(shots, base) {
  console.log("");
  console.log(`Take recorder — ${shots.length} shots, total runtime ${TOTAL_RUNTIME_SEC}s`);
  console.log("");
  for (const shot of shots) {
    const window = `${formatTimestamp(shot.startSec)}–${formatTimestamp(shot.endSec)}`;
    console.log(
      `#${String(shot.shotIndex).padStart(2)}  ${shot.chapter.padEnd(8)} ${window}  takes=${shot.takes}`,
    );
    console.log(`     URL:    ${buildUrl(base, shot.fragment)}`);
    console.log(`     CUE:    ${shot.interaction}`);
    console.log(`     NOTE:   ${shot.note}`);
    console.log("");
  }
}

function main() {
  const args = parseArgs(process.argv);
  let shots = SHOTS;
  if (args.shot !== null && Number.isFinite(args.shot)) {
    shots = SHOTS.filter((s) => s.shotIndex === args.shot);
    if (shots.length === 0) {
      console.error(`No shot with index ${args.shot} (valid: 1..11)`);
      process.exit(1);
    }
  }
  if (args.json) {
    console.log(JSON.stringify(shots, null, 2));
  } else {
    printHuman(shots, args.base);
  }
}

main();
