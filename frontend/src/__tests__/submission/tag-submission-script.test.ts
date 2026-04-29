/**
 * W5 Driver D — T5.D.3
 *
 * Git tag automation script: `scripts/tag-submission.mjs` creates the
 * annotated `v0.1.0-hackfw-submission` tag and pushes it to origin.
 *
 * The script is intentionally read-only on the working tree. It refuses
 * to run with uncommitted changes. It reads the submission summary
 * (test counts, Lighthouse scores, deployment URL) from a structured
 * env or the submission-checklist sign-off block.
 */
import { describe, it, expect } from "vitest";
import { existsSync, readFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";

const REPO_ROOT = resolve(__dirname, "..", "..", "..", "..");
const SCRIPT = join(REPO_ROOT, "scripts", "tag-submission.mjs");

function read(): string {
  return readFileSync(SCRIPT, "utf8");
}

describe("Tag-submission script (T5.D.3)", () => {
  it("file exists and is non-trivial", () => {
    expect(existsSync(SCRIPT)).toBe(true);
    expect(statSync(SCRIPT).size).toBeGreaterThanOrEqual(1500);
  });

  it("declares the canonical tag name v0.1.0-hackfw-submission", () => {
    expect(read()).toMatch(/v0\.1\.0-hackfw-submission/);
  });

  it("verifies working tree is clean before tagging", () => {
    const src = read();
    expect(src).toMatch(/git status --porcelain|working tree.*clean|--porcelain/);
  });

  it("verifies branch is sprint/visual-rebirth or main before tagging", () => {
    const src = read();
    expect(src).toMatch(/sprint\/visual-rebirth|sprint\/w5-submission|main/);
  });

  it("creates an annotated tag (-a) with a structured message", () => {
    const src = read();
    expect(src).toMatch(/git tag -a|git tag --annotate/);
    // Message can be passed via -m, --message, or -F (file/stdin); the
    // structured message itself must be assembled in the script.
    expect(src).toMatch(/-m\b|--message|-F\b|--file/);
    // Structured message body (operator-readable) must mention sprint
    // summary anchors.
    expect(src).toMatch(/HackFW|Submission|Test count|tests passing/i);
  });

  it("pushes the tag to origin", () => {
    const src = read();
    // Script template-interpolates the tag name; match either form.
    expect(src).toMatch(
      /git push origin\s+(v0\.1\.0-hackfw-submission|\$\{TAG_NAME\}|--tags)/,
    );
  });

  it("supports a --dry-run flag for safety", () => {
    expect(read()).toMatch(/--dry-run|dry[- ]run/);
  });

  it("emits a confirmation + tag URL on success", () => {
    const src = read();
    expect(src).toMatch(/github\.com\/fivedollarfridays\/montgowork|releases\/tag/);
  });

  it("includes the sprint summary (test counts, Lighthouse, deployment URL)", () => {
    const src = read();
    expect(src).toMatch(/test count|tests passing|vitest|pytest/i);
    expect(src).toMatch(/Lighthouse|First Load JS|bundle/i);
  });

  it("references the submission-checklist (T+15min step)", () => {
    const checklist = readFileSync(
      join(REPO_ROOT, "docs", "submission-checklist.md"),
      "utf8",
    );
    // The checklist's T+15min block already mentions tag creation; this
    // test guards that the script and the checklist agree on the tag name.
    expect(checklist).toMatch(/v0\.1\.0-hackfw-submission/);
    expect(checklist).toMatch(/tag-submission|scripts\/tag-submission|node scripts\/tag-submission/);
  });
});
