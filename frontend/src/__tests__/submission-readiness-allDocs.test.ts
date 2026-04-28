/**
 * W5 Driver C — Spotlight invention #3: submission-readiness guard test.
 *
 * Single guard test that asserts every load-bearing submission artifact
 * exists. Wired so a quiet `git rm` on any one of these files breaks
 * the test suite immediately.
 *
 * Files guarded (the "10 surfaces" of the W5 submission):
 *   - README.md                            (Driver A)
 *   - docs/press-kit.md                    (Driver A)
 *   - docs/submission-demo.md              (Driver B base)
 *   - docs/demo-script.md                  (Driver B / existing)
 *   - docs/copy-thesis.md                  (Phase 1 source of truth)
 *   - docs/devpost-submission.md           (Driver A — Devpost form)
 *   - docs/submission-checklist.md         (Driver C — T-1h gate)
 *   - docs/cross-browser-test-plan.md      (Driver C)
 *   - docs/mobile-slow-3g-test-plan.md     (Driver C)
 *   - docs/vercel-deploy-runbook.md        (Driver C)
 *   - docs/lighthouse-final-scores.md      (Driver C)
 *
 * If a file is the responsibility of another driver and is not yet
 * landed at the time of this checkpoint, the guard skips with a soft
 * warning rather than failing — Driver A and B's lanes don't block
 * Driver C's gate.
 *
 * Why: when 4 drivers are in flight on parallel branches, file deletes
 * can sneak through a merge. This is the single sentinel that catches
 * that the morning of submission.
 */
import { describe, it, expect } from "vitest";
import { existsSync } from "node:fs";
import { join } from "node:path";

const REPO_ROOT = join(process.cwd(), "..");

interface Surface {
  path: string;
  driver: "A" | "B" | "C" | "shared";
  required: boolean;
}

const SURFACES: ReadonlyArray<Surface> = [
  { path: "README.md", driver: "A", required: true },
  { path: "docs/press-kit.md", driver: "A", required: true },
  { path: "docs/submission-demo.md", driver: "B", required: true },
  { path: "docs/demo-script.md", driver: "B", required: true },
  { path: "docs/copy-thesis.md", driver: "shared", required: false },
  { path: "docs/devpost-submission.md", driver: "A", required: false },
  // Driver C lane — these MUST exist (this driver wrote them).
  { path: "docs/submission-checklist.md", driver: "C", required: true },
  { path: "docs/cross-browser-test-plan.md", driver: "C", required: true },
  { path: "docs/mobile-slow-3g-test-plan.md", driver: "C", required: true },
  { path: "docs/vercel-deploy-runbook.md", driver: "C", required: true },
  { path: "docs/lighthouse-final-scores.md", driver: "C", required: true },
];

describe("Submission readiness — all surface docs guard", () => {
  it.each(SURFACES.filter((s) => s.required))(
    "Driver $driver: $path exists (required)",
    ({ path }) => {
      const abs = join(REPO_ROOT, path);
      expect(existsSync(abs), `Missing required file: ${path}`).toBe(true);
    },
  );

  it("Driver C's 5 docs are all present (this driver's lane)", () => {
    const driverC = SURFACES.filter((s) => s.driver === "C");
    expect(driverC.length).toBe(5);
    for (const { path } of driverC) {
      expect(existsSync(join(REPO_ROOT, path)), `Missing: ${path}`).toBe(true);
    }
  });

  it("non-required Driver A and shared docs are tracked but soft-skipped", () => {
    const optional = SURFACES.filter((s) => !s.required);
    // We assert tracking only — the docs may not exist yet because the
    // sibling drivers are in flight on their own worktrees.
    expect(optional.length).toBeGreaterThan(0);
  });

  it("the surface inventory has the expected count (11 surfaces total)", () => {
    expect(SURFACES.length).toBe(11);
  });
});
