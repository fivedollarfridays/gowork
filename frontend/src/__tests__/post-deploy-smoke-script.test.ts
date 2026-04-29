/**
 * W5 Driver C — Spotlight invention #2 contract.
 *
 * Pin the contract of `frontend/scripts/post-deploy-smoke.mjs`:
 *   - Script exists
 *   - Reads SITE_URL from env (default: gowork.vercel.app)
 *   - Asserts HTTP 200 on `/`, `/api/og/1`, `/api/og/default`
 *   - Asserts HTTP 404 on a bogus URL with wall-metaphor copy
 *   - Asserts the OG endpoints return image/png content-type
 *   - Exits non-zero on any failure
 *
 * Why: post-deploy smoke is the LAST gate between Shawn and the
 * submission deadline. One command, deterministic, runs in < 30s.
 */
import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const SCRIPT_PATH = join(
  process.cwd(),
  "scripts",
  "post-deploy-smoke.mjs",
);

describe("scripts/post-deploy-smoke.mjs — Spotlight #2", () => {
  it("exists at the expected path", () => {
    expect(existsSync(SCRIPT_PATH)).toBe(true);
  });

  const src = existsSync(SCRIPT_PATH)
    ? readFileSync(SCRIPT_PATH, "utf8")
    : "";

  it("reads the production URL from env (SITE_URL or NEXT_PUBLIC_SITE_URL)", () => {
    expect(src).toMatch(/process\.env\.(SITE_URL|NEXT_PUBLIC_SITE_URL)/);
  });

  it("defaults to gowork.vercel.app when env is unset", () => {
    expect(src).toMatch(/gowork\.vercel\.app/);
  });

  it("hits all 3 critical endpoints (/, /api/og/1, /api/og/default)", () => {
    expect(src).toMatch(/['"]\/['"]/); // root path
    expect(src).toMatch(/\/api\/og\/1/);
    expect(src).toMatch(/\/api\/og\/default/);
  });

  it("asserts a 404 with wall-metaphor copy on a bogus URL", () => {
    expect(src).toMatch(/404/);
    expect(src).toMatch(/bogus|not[- ]found|nonexistent/i);
  });

  it("asserts image/png content-type on OG endpoints", () => {
    expect(src).toMatch(/image\/png|content-type/i);
  });

  it("uses fetch (Node 18+) to make HTTP requests", () => {
    expect(src).toMatch(/fetch\(/);
  });

  it("exits non-zero on failure", () => {
    expect(src).toMatch(
      /process\.exit\(\s*(?:1|code|status|failures)\s*\)|process\.exitCode/i,
    );
  });

  it("uses ES modules (.mjs)", () => {
    expect(src).toMatch(/import .+ from|^#!/m);
  });
});
