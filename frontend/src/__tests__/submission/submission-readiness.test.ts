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
  // W5 Driver D — extended cross-document linking sweep (T5.D.4)
  {
    path: "docs/submission-checklist.md",
    minBytes: 1500,
    reason: "T-1h Death Note checklist (Driver C)",
  },
  {
    path: "docs/vercel-deploy-runbook.md",
    minBytes: 1500,
    reason: "Production deploy runbook (Driver C)",
  },
  {
    path: "docs/submission-video-script.md",
    minBytes: 1500,
    reason: "Submission video script (Driver B)",
  },
  {
    path: "docs/submission-video-take-plan.md",
    minBytes: 1000,
    reason: "Submission video take plan (Driver B)",
  },
  {
    path: "docs/submission-video.srt",
    minBytes: 500,
    reason: "Submission video captions (Driver B)",
  },
  {
    path: "docs/post-submission/reddit-r-civic-tech.md",
    minBytes: 1500,
    reason: "Driver D — Reddit announcement draft",
  },
  {
    path: "docs/post-submission/twitter-thread.md",
    minBytes: 800,
    reason: "Driver D — Twitter / X thread draft",
  },
  {
    path: "docs/post-submission/linkedin-announcement.md",
    minBytes: 2000,
    reason: "Driver D — LinkedIn announcement draft",
  },
  {
    path: "docs/post-submission/post-mortem-template.md",
    minBytes: 1500,
    reason: "Driver D — Post-HackFW post-mortem template",
  },
  {
    path: "scripts/tag-submission.mjs",
    minBytes: 1500,
    reason: "Driver D — git tag automation script",
  },
  {
    path: "LICENSE",
    minBytes: 1000,
    reason: "MIT license (referenced by README)",
  },
];

const REQUIRED_DIRS = [
  { path: "docs/press-kit", reason: "press kit assets" },
  { path: "docs/post-submission", reason: "Driver D — post-submission drafts" },
];

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

  it("README pins the audience-facing surface (no submission-only spokes)", () => {
    // Narrative reset (sprint/narrative-reset, commit 03dff3c): the
    // README was rewritten as a public, audience-facing entry point —
    // submission-only spokes (press-kit, Devpost form, post-submission
    // drafts) were stripped. Judges find the submission packet via the
    // Devpost form, not via README. What MUST stay: project name,
    // Fort Worth framing, MIT license, at least one architecture or
    // setup doc link.
    const md = readFileSync(join(REPO_ROOT, "README.md"), "utf8");
    expect(md).toMatch(/GoWork/);
    expect(md).toMatch(/Fort Worth/i);
    expect(md).toMatch(/MIT/);
  });

  it("README links to at least one architecture or setup doc (T5.D.4)", () => {
    // Narrative reset stripped the W5-D submission-checklist and
    // vercel-deploy-runbook spokes from the README — those docs still
    // exist (covered by REQUIRED_FILES above) but they're not load-
    // bearing for the public-facing surface. A contributor must still
    // be able to walk from README to one architecture-level doc.
    const md = readFileSync(join(REPO_ROOT, "README.md"), "utf8");
    expect(md).toMatch(/docs\/(architecture|setup|api|DEPLOYMENT)\.md/i);
  });

  it("README documents the docs/ directory as the discoverability surface (T5.D.4)", () => {
    // Narrative reset rewrote the Documentation section as a flat
    // table of audience-facing docs (setup, api, architecture,
    // SECURITY, DEPLOYMENT, demo-script, ROADMAP). Post-submission
    // drafts live under docs/post-submission/ and are not linked
    // from README anymore — they're internal scaffolding for the
    // announcement wave. We assert the audience-facing docs table
    // is present instead.
    const md = readFileSync(join(REPO_ROOT, "README.md"), "utf8");
    expect(md).toMatch(/##\s*Documentation/i);
    expect(md).toMatch(/ROADMAP\.md|docs\/setup\.md/i);
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
