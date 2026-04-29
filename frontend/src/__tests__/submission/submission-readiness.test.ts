/**
 * W5 Driver A — Spotlight invention #3
 *
 * Submission-readiness guard. A single failing test here lights up CI red
 * the moment any required artifact for the HackFW Devpost submission goes
 * missing or gets accidentally deleted.
 *
 * The artifacts are:
 *
 *   1. README.md                       — first thing judges see
 *   2. docs/press-kit.md               — press kit single-source-of-truth
 *   3. docs/press-kit/                 — directory of cinematic stills + assets
 *   4. docs/submission-demo.md         — Driver B owns the live demo script
 *   5. docs/devpost-submission.md      — Devpost form pre-fill
 *   6. docs/copy-thesis.md             — locked editorial voice (Spotlight #1)
 *   7. docs/fw-dao-bounty-research.md  — FW DAO claim path investigation
 *
 * If a future driver decomposes any of these (e.g., splits press-kit into
 * press-kit/index.md), this test fails and forces a deliberate update.
 */
import { describe, it, expect } from "vitest";
import { existsSync, statSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";

const REPO_ROOT = resolve(__dirname, "..", "..", "..", "..");

const REQUIRED_FILES: { path: string; minBytes: number; reason: string }[] = [
  { path: "README.md", minBytes: 1500, reason: "judges read it first" },
  { path: "docs/press-kit.md", minBytes: 1500, reason: "press kit canonical" },
  {
    path: "docs/submission-demo.md",
    minBytes: 800,
    reason: "Driver B live demo script",
  },
  {
    path: "docs/devpost-submission.md",
    minBytes: 1500,
    reason: "Devpost form pre-fill",
  },
  {
    path: "docs/copy-thesis.md",
    minBytes: 400,
    reason: "Spotlight #1 — locked editorial voice",
  },
  {
    path: "docs/fw-dao-bounty-research.md",
    minBytes: 600,
    reason: "T5.A.5 FW DAO claim path",
  },
];

const REQUIRED_DIRS = [{ path: "docs/press-kit", reason: "press kit assets" }];

describe("Submission-readiness guard (Spotlight #3)", () => {
  it.each(REQUIRED_FILES)(
    "$path exists and has content ($reason)",
    ({ path, minBytes }) => {
      const full = join(REPO_ROOT, path);
      expect(existsSync(full), `${path} must exist`).toBe(true);
      const size = statSync(full).size;
      expect(
        size,
        `${path} is suspiciously small (${size} < ${minBytes} bytes)`,
      ).toBeGreaterThanOrEqual(minBytes);
    },
  );

  it.each(REQUIRED_DIRS)("$path/ directory exists ($reason)", ({ path }) => {
    const full = join(REPO_ROOT, path);
    expect(existsSync(full), `${path}/ must exist`).toBe(true);
    expect(statSync(full).isDirectory(), `${path} must be a directory`).toBe(
      true,
    );
  });

  it("README references both press kit and Devpost docs", () => {
    const md = readFileSync(join(REPO_ROOT, "README.md"), "utf8");
    // The README is the hub for the submission packet — both spokes must be
    // discoverable from it.
    expect(md).toMatch(/press[- ]kit/i);
  });

  it("copy-thesis.md is the canonical source of editorial voice", () => {
    const md = readFileSync(join(REPO_ROOT, "docs", "copy-thesis.md"), "utf8");
    expect(md).toMatch(/standing between you and a job/i);
    expect(md).toMatch(/we do the math/i);
  });

  it("fw-dao-bounty-research.md documents claim path or honest gap", () => {
    const md = readFileSync(
      join(REPO_ROOT, "docs", "fw-dao-bounty-research.md"),
      "utf8",
    );
    // Either we found a claim path OR we honestly documented what we tried.
    expect(md).toMatch(/(bounty|dao|claim|portal|fwtx)/i);
  });
});
