#!/usr/bin/env node
/**
 * W5 Driver D — Spotlight invention.
 *
 * scripts/release-notes-generator.mjs
 *
 * Generates structured release notes from `git log` between two tags.
 *
 * Designed to support the post-submission release cadence:
 *
 *   v0.1.0-hackfw-submission  →  v0.2.0-fw-deploy        (post-judging)
 *   v0.2.0-fw-deploy          →  v0.3.0-multi-city       (Dallas)
 *   v0.3.0-multi-city         →  v0.4.0-...
 *
 * Usage:
 *
 *   node scripts/release-notes-generator.mjs --from=v0.1.0 --to=HEAD
 *   node scripts/release-notes-generator.mjs --from=v0.1.0 --to=v0.2.0 > RELEASE-NOTES-v0.2.0.md
 *   node scripts/release-notes-generator.mjs --from=v0.1.0-hackfw-submission --json
 *
 * Categorizes commits by Conventional Commit prefix:
 *   - feat / feature → "Features"
 *   - fix → "Bug fixes"
 *   - refactor → "Refactors"
 *   - chore / docs / test → "Housekeeping"
 *   - merge → grouped under their nested commits (best effort)
 */
import { execSync } from "node:child_process";
import { argv, exit } from "node:process";

// ─────────────────────────────────────────────────────────────
// Arg parsing
// ─────────────────────────────────────────────────────────────
const args = argv.slice(2);
function flagValue(name) {
  const a = args.find((s) => s.startsWith(`--${name}=`));
  return a ? a.slice(name.length + 3) : undefined;
}
const FROM = flagValue("from");
const TO = flagValue("to") ?? "HEAD";
const json = args.includes("--json");
const help = args.includes("--help") || args.includes("-h");

if (help || !FROM) {
  console.log(`
release-notes-generator.mjs — generate release notes from git log.

Required:
  --from=<tag-or-sha>   Starting commit (exclusive)

Optional:
  --to=<tag-or-sha>     Ending commit (default: HEAD)
  --json                Emit structured JSON instead of markdown

Example:
  node scripts/release-notes-generator.mjs --from=v0.1.0-hackfw-submission --to=HEAD
  node scripts/release-notes-generator.mjs --from=v0.1.0 --to=v0.2.0 > RELEASE-NOTES.md
`);
  exit(FROM ? 0 : 2);
}

function sh(cmd) {
  return execSync(cmd, { encoding: "utf8" }).trim();
}

// ─────────────────────────────────────────────────────────────
// Read commits (oneline, no merges by default — we keep merges so the
// PR-merge story is intact)
// ─────────────────────────────────────────────────────────────
let log;
try {
  log = sh(`git log ${FROM}..${TO} --pretty=format:%H%x09%s%x09%an%x09%aI`);
} catch (err) {
  console.error(`Could not read git log ${FROM}..${TO}.`);
  console.error(`Are both refs valid? Run: git tag --list && git log --oneline -5`);
  exit(1);
}

const commits = log
  .split("\n")
  .filter(Boolean)
  .map((line) => {
    const [sha, subject, author, date] = line.split("\t");
    return { sha, subject, author, date };
  });

// ─────────────────────────────────────────────────────────────
// Categorize
// ─────────────────────────────────────────────────────────────
const categories = {
  features: [],
  fixes: [],
  refactors: [],
  docs: [],
  chores: [],
  tests: [],
  merges: [],
  other: [],
};

const conventionalPrefix = /^(feat|feature|fix|refactor|chore|docs|test|perf|style|build|ci|merge|revert)(?:\([^)]+\))?(!)?:\s*(.*)$/i;

for (const c of commits) {
  const m = c.subject.match(conventionalPrefix);
  if (!m) {
    if (/^merge\b/i.test(c.subject)) {
      categories.merges.push(c);
    } else {
      categories.other.push(c);
    }
    continue;
  }
  const kind = m[1].toLowerCase();
  const message = m[3];
  const entry = { ...c, message };
  switch (kind) {
    case "feat":
    case "feature":
      categories.features.push(entry);
      break;
    case "fix":
      categories.fixes.push(entry);
      break;
    case "refactor":
    case "perf":
      categories.refactors.push(entry);
      break;
    case "docs":
      categories.docs.push(entry);
      break;
    case "test":
      categories.tests.push(entry);
      break;
    case "chore":
    case "build":
    case "ci":
    case "style":
      categories.chores.push(entry);
      break;
    case "merge":
    case "revert":
      categories.merges.push(entry);
      break;
    default:
      categories.other.push(entry);
  }
}

// ─────────────────────────────────────────────────────────────
// Render
// ─────────────────────────────────────────────────────────────
if (json) {
  console.log(
    JSON.stringify(
      {
        from: FROM,
        to: TO,
        totalCommits: commits.length,
        generatedAt: new Date().toISOString(),
        categories,
      },
      null,
      2,
    ),
  );
  exit(0);
}

const fromDate = (() => {
  try {
    return sh(`git log -1 --format=%aI ${FROM}`);
  } catch {
    return "";
  }
})();

const toDate = (() => {
  try {
    return sh(`git log -1 --format=%aI ${TO}`);
  } catch {
    return "";
  }
})();

console.log(`# Release notes: ${FROM} → ${TO}`);
console.log("");
console.log(`Generated ${new Date().toISOString().slice(0, 10)} from \`git log ${FROM}..${TO}\`.`);
console.log("");
console.log(`- **From:** \`${FROM}\` (${fromDate || "unknown date"})`);
console.log(`- **To:** \`${TO}\` (${toDate || "unknown date"})`);
console.log(`- **Total commits:** ${commits.length}`);
console.log("");

function section(title, list) {
  if (list.length === 0) return;
  console.log(`## ${title}`);
  console.log("");
  for (const c of list) {
    const sha = c.sha.slice(0, 7);
    const msg = c.message ?? c.subject;
    console.log(`- ${msg} (\`${sha}\`, ${c.author})`);
  }
  console.log("");
}

section("Features", categories.features);
section("Bug fixes", categories.fixes);
section("Refactors / performance", categories.refactors);
section("Documentation", categories.docs);
section("Tests", categories.tests);
section("Housekeeping (chore / build / ci / style)", categories.chores);
section("Merges", categories.merges);
section("Other / uncategorized", categories.other);

console.log("---");
console.log("");
console.log(
  `Generated by \`scripts/release-notes-generator.mjs\` (W5 Driver D Spotlight).`,
);
console.log(
  `See \`docs/post-submission/post-mortem-template.md\` for the post-mortem flow.`,
);
