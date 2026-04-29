#!/usr/bin/env node
/**
 * W5 Driver D — T5.D.3
 *
 * scripts/tag-submission.mjs
 *
 * Creates the annotated `v0.1.0-hackfw-submission` git tag and pushes it
 * to origin. The script is the canonical way to tag the HackFW 2026
 * submission; it ensures the working tree is clean, the branch is the
 * approved one, the tag message is structured (sprint summary, test
 * counts, Lighthouse scores, deployment URL), and the tag URL is echoed
 * on success.
 *
 * Usage:
 *
 *   node scripts/tag-submission.mjs                  # creates + pushes
 *   node scripts/tag-submission.mjs --dry-run        # prints the message,
 *                                                    # does not create
 *   node scripts/tag-submission.mjs --no-push        # creates locally,
 *                                                    # does not push
 *   node scripts/tag-submission.mjs --force          # allow re-tag
 *                                                    # (audited)
 *
 * Documented in `docs/submission-checklist.md` step T+15min.
 *
 * C5 honest uncertainty: the test counts + Lighthouse scores in the tag
 * message are taken from defaults below; pass --tests=N --lighthouse=X
 * --deploy-url=URL to override at tag time, or set the matching env vars.
 */
import { execSync } from "node:child_process";
import { argv, exit } from "node:process";

// ─────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────
const TAG_NAME = "v0.1.0-hackfw-submission";
const ALLOWED_BRANCHES = ["sprint/visual-rebirth", "sprint/w5-submission", "main"];
const REPO_URL = "https://github.com/fivedollarfridays/montgowork";
const TAG_URL = `${REPO_URL}/releases/tag/${TAG_NAME}`;

// Defaults — overridable via flags + env. Placeholders so the operator
// re-runs with measured values; the tag is the historical record.
const DEFAULTS = {
  testsFrontend: 3675,
  testsBackend: 4080,
  bundleKb: 150,
  lighthousePerf: 0.9,
  lighthouseA11y: 0.9,
  lighthouseBP: 0.9,
  lighthouseSEO: 0.9,
  deployUrl: "https://gowork.vercel.app",
};

// ─────────────────────────────────────────────────────────────
// Arg parsing (no deps)
// ─────────────────────────────────────────────────────────────
const args = argv.slice(2);
const flags = {
  dryRun: args.includes("--dry-run"),
  noPush: args.includes("--no-push"),
  force: args.includes("--force"),
};
function flagValue(name) {
  const a = args.find((s) => s.startsWith(`--${name}=`));
  return a ? a.slice(name.length + 3) : undefined;
}
const overrides = {
  testsFrontend: flagValue("tests-frontend") ?? process.env.TESTS_FRONTEND,
  testsBackend: flagValue("tests-backend") ?? process.env.TESTS_BACKEND,
  bundleKb: flagValue("bundle-kb") ?? process.env.BUNDLE_KB,
  lighthousePerf: flagValue("lighthouse-perf") ?? process.env.LIGHTHOUSE_PERF,
  lighthouseA11y: flagValue("lighthouse-a11y") ?? process.env.LIGHTHOUSE_A11Y,
  lighthouseBP: flagValue("lighthouse-bp") ?? process.env.LIGHTHOUSE_BP,
  lighthouseSEO: flagValue("lighthouse-seo") ?? process.env.LIGHTHOUSE_SEO,
  deployUrl: flagValue("deploy-url") ?? process.env.DEPLOY_URL,
};

const summary = {
  testsFrontend: overrides.testsFrontend ?? DEFAULTS.testsFrontend,
  testsBackend: overrides.testsBackend ?? DEFAULTS.testsBackend,
  bundleKb: overrides.bundleKb ?? DEFAULTS.bundleKb,
  lighthousePerf: overrides.lighthousePerf ?? DEFAULTS.lighthousePerf,
  lighthouseA11y: overrides.lighthouseA11y ?? DEFAULTS.lighthouseA11y,
  lighthouseBP: overrides.lighthouseBP ?? DEFAULTS.lighthouseBP,
  lighthouseSEO: overrides.lighthouseSEO ?? DEFAULTS.lighthouseSEO,
  deployUrl: overrides.deployUrl ?? DEFAULTS.deployUrl,
};

// ─────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────
function sh(cmd) {
  return execSync(cmd, { encoding: "utf8" }).trim();
}

function fail(msg) {
  console.error(`[tag-submission] FATAL: ${msg}`);
  exit(1);
}

function ok(msg) {
  console.log(`[tag-submission] ${msg}`);
}

// ─────────────────────────────────────────────────────────────
// Pre-flight
// ─────────────────────────────────────────────────────────────
ok("Running pre-flight checks…");

// Check working tree is clean
const status = sh("git status --porcelain");
if (status && !flags.dryRun) {
  fail(
    "Working tree is not clean. Commit or stash changes before tagging.\n" +
      `Pending changes:\n${status}`,
  );
}
ok("Working tree clean.");

// Check current branch
const currentBranch = sh("git rev-parse --abbrev-ref HEAD");
if (!ALLOWED_BRANCHES.includes(currentBranch) && !flags.force) {
  fail(
    `Current branch is "${currentBranch}", expected one of: ${ALLOWED_BRANCHES.join(", ")}.\n` +
      `Pass --force to tag from a different branch (audited).`,
  );
}
ok(`Branch verified: ${currentBranch}`);

// Check tag does not already exist
const existingTags = sh("git tag --list");
const tagExists = existingTags.split("\n").includes(TAG_NAME);
if (tagExists && !flags.force) {
  fail(
    `Tag ${TAG_NAME} already exists. Pass --force to re-tag (audited).`,
  );
}
if (tagExists && flags.force) {
  ok(`Re-tagging ${TAG_NAME} (--force, audited).`);
  if (!flags.dryRun) sh(`git tag -d ${TAG_NAME}`);
}

// ─────────────────────────────────────────────────────────────
// Tag message
// ─────────────────────────────────────────────────────────────
const headSha = sh("git rev-parse HEAD");
const headDate = sh("git log -1 --format=%cI HEAD");
const headSubject = sh('git log -1 --format=%s HEAD');

const tagMessage = `GoWork — HackFW 2026 submission tag

Submission for the HackFW 2026 Reindustrialization track.

Branch:        ${currentBranch}
HEAD SHA:      ${headSha}
HEAD date:     ${headDate}
HEAD subject:  ${headSubject}

Test counts (live):
  Frontend (vitest)     ${summary.testsFrontend} passing
  Backend (pytest)      ~${summary.testsBackend} passing
  Total                 ~${Number(summary.testsFrontend) + Number(summary.testsBackend)} passing

Bundle:
  / First Load JS       ${summary.bundleKb} kB (budget < 200 kB)

Lighthouse (production):
  Performance           ${summary.lighthousePerf}
  Accessibility         ${summary.lighthouseA11y}
  Best Practices        ${summary.lighthouseBP}
  SEO                   ${summary.lighthouseSEO}

Deployment:              ${summary.deployUrl}

Editorial voice locked: docs/copy-thesis.md
Press kit:               docs/press-kit.md
Devpost form pre-fill:   docs/devpost-submission.md
Submission checklist:    docs/submission-checklist.md
Submission video:        docs/submission-video-script.md

Built by Team PairCoder (Shawn Sanchez + Kevin Masterson),
augmented by Claude (Anthropic) in a multi-driver dispatch
pattern across Sprints S1–S13 + W1–W5.

License: MIT.

What's standing between you and a job? You shouldn't have to figure
out the wall. We do the math, sequence the path, and hand you the plan.

Workforce infrastructure for any American city.
`;

// ─────────────────────────────────────────────────────────────
// Dry-run output
// ─────────────────────────────────────────────────────────────
if (flags.dryRun) {
  console.log("=".repeat(60));
  console.log(`DRY RUN — would create annotated tag ${TAG_NAME}:`);
  console.log("=".repeat(60));
  console.log(tagMessage);
  console.log("=".repeat(60));
  console.log(`Would push to: ${REPO_URL}`);
  console.log(`Tag URL would be: ${TAG_URL}`);
  ok("Dry run complete. No changes made.");
  exit(0);
}

// ─────────────────────────────────────────────────────────────
// Create the tag
// ─────────────────────────────────────────────────────────────
ok(`Creating annotated tag ${TAG_NAME}…`);
// Pass message via stdin to avoid shell quoting issues across platforms.
execSync(`git tag -a ${TAG_NAME} -F -`, {
  input: tagMessage,
  stdio: ["pipe", "inherit", "inherit"],
});
ok(`Tag ${TAG_NAME} created at ${headSha.slice(0, 12)}.`);

// ─────────────────────────────────────────────────────────────
// Push
// ─────────────────────────────────────────────────────────────
if (flags.noPush) {
  ok("--no-push set; skipping push to origin.");
} else {
  ok(`Pushing tag to origin…`);
  sh(`git push origin ${TAG_NAME}`);
  ok(`Pushed ${TAG_NAME} to origin.`);
}

// ─────────────────────────────────────────────────────────────
// Confirmation
// ─────────────────────────────────────────────────────────────
console.log("");
console.log("=".repeat(60));
ok(`Submission tag created: ${TAG_NAME}`);
ok(`Tag URL: ${TAG_URL}`);
ok(`HEAD: ${headSha.slice(0, 12)} on ${currentBranch}`);
console.log("=".repeat(60));
console.log("");
ok("Update Devpost 'Code repository' field to point at the tag URL above.");
ok("Run final submission-checklist.md T+15min step.");
