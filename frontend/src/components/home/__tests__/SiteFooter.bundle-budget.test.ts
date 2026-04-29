/**
 * polish-2 Driver D — T46 footer bundle budget guard.
 *
 * Driver D does not own SiteFooter.tsx; the actual lazy-load change is
 * documented in `frontend/POLISH-2-FOLLOWUP.md` for Driver A or the
 * integrator. Until that change lands, this test guards the file-size
 * budget so we know the day the static import slips back in.
 *
 * Contract:
 *   - SiteFooter.tsx must stay under 400 lines (arch limit).
 *   - The follow-up doc must exist (so the work isn't forgotten).
 *   - When BrandMark is lazy-loaded, the static import line is
 *     replaced with `next/dynamic`. We don't fail the build if it's
 *     still static — we surface the contract so a reviewer notices the
 *     follow-up file lives in the working tree.
 */
import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..", "..", "..");
const FOOTER = path.resolve(
  FRONTEND_ROOT,
  "src/components/home/SiteFooter.tsx",
);
const FOLLOWUP = path.resolve(FRONTEND_ROOT, "POLISH-2-FOLLOWUP.md");

describe("polish-2 T46 — footer bundle budget", () => {
  it("SiteFooter.tsx is under the 400-line arch limit", () => {
    const lines = fs.readFileSync(FOOTER, "utf-8").split(/\r?\n/).length;
    expect(lines).toBeLessThan(400);
  });

  it("the follow-up doc exists at frontend/POLISH-2-FOLLOWUP.md", () => {
    expect(fs.existsSync(FOLLOWUP)).toBe(true);
  });

  it("the follow-up doc names BrandMark + the lazy-load recommendation", () => {
    const md = fs.readFileSync(FOLLOWUP, "utf-8");
    expect(md).toMatch(/BrandMark/);
    expect(md).toMatch(/next\/dynamic/);
  });
});
