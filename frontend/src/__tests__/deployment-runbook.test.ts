/**
 * W5 Driver C — T5.C.6 part 3.
 *
 * Asserts `docs/vercel-deploy-runbook.md` covers every required section so
 * Shawn (or whoever) can ship a production deploy at 6 AM CDT on May 2
 * without spelunking 8 different docs.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const RUNBOOK_PATH = join(
  process.cwd(),
  "..",
  "docs",
  "vercel-deploy-runbook.md",
);

describe("docs/vercel-deploy-runbook.md", () => {
  const doc = readFileSync(RUNBOOK_PATH, "utf8");

  it("exists with non-trivial content (> 2 KB)", () => {
    expect(doc.length).toBeGreaterThan(2000);
  });

  it("documents pre-deploy gates (build, tests, contrast, lighthouse)", () => {
    expect(doc).toMatch(/Pre-?deploy/i);
    expect(doc).toMatch(/build/i);
    expect(doc).toMatch(/test|vitest/i);
    expect(doc).toMatch(/Lighthouse/i);
  });

  it("specifies Vercel project setup (root directory + framework)", () => {
    expect(doc).toMatch(/Vercel/);
    expect(doc).toMatch(/Root Directory/i);
    expect(doc).toMatch(/frontend\//);
    expect(doc).toMatch(/Next\.?js/i);
  });

  it("enumerates all 5 required NEXT_PUBLIC env vars", () => {
    expect(doc).toMatch(/NEXT_PUBLIC_API_URL/);
    expect(doc).toMatch(/NEXT_PUBLIC_MAPBOX_TOKEN/);
    expect(doc).toMatch(/NEXT_PUBLIC_MAPBOX_STYLE_URL/);
    expect(doc).toMatch(/NEXT_PUBLIC_LAST_CALIBRATED/);
    expect(doc).toMatch(/NEXT_PUBLIC_SITE_URL/);
  });

  it("explains where to obtain a Mapbox token", () => {
    expect(doc).toMatch(/account\.mapbox\.com\/access-tokens/);
  });

  it("documents staging→production promotion path", () => {
    expect(doc).toMatch(/staging|preview/i);
    expect(doc).toMatch(/production/i);
    expect(doc).toMatch(/promot/i);
  });

  it("specifies a smoke test post-deploy with concrete URLs", () => {
    expect(doc).toMatch(/smoke/i);
    expect(doc).toMatch(/\/api\/og\/1/);
    expect(doc).toMatch(/\/api\/og\/default/);
  });

  it("documents the 404 wall-metaphor smoke check", () => {
    expect(doc).toMatch(/404/);
    expect(doc).toMatch(/wall|EN.{0,10}ES|Spanish/i);
  });

  it("documents a rollback path", () => {
    expect(doc).toMatch(/Rollback/i);
    expect(doc).toMatch(/revert|previous|redeploy/i);
  });

  it("specifies the Vercel project name 'gowork'", () => {
    expect(doc).toMatch(/gowork/);
  });

  it("documents how to set NEXT_PUBLIC_LAST_CALIBRATED at deploy time", () => {
    expect(doc).toMatch(/NEXT_PUBLIC_LAST_CALIBRATED/);
    expect(doc).toMatch(/each deploy|every deploy|deploy time|update at/i);
  });
});
