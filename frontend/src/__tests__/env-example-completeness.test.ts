/**
 * W5 Driver C — T5.C.6 part 2.
 *
 * Asserts `frontend/.env.local.example` enumerates every NEXT_PUBLIC_*
 * variable required to run a production deploy.
 *
 * Required set (locked in W5 Driver C brief):
 *   - NEXT_PUBLIC_API_URL — backend base URL
 *   - NEXT_PUBLIC_MAPBOX_TOKEN — Mapbox access token (Wall map)
 *   - NEXT_PUBLIC_MAPBOX_STYLE_URL — custom dark editorial style
 *   - NEXT_PUBLIC_LAST_CALIBRATED — Live Now widget (W4 A)
 *   - NEXT_PUBLIC_SITE_URL — absolute OG/Twitter image URLs (W4 D)
 *
 * Why this test: a quiet missing var blows up Vercel deploy at build OR at
 * first request. The env example IS our deployment contract — if a key
 * here is missing or rot-bit, the runbook lies. This test makes the lie
 * impossible.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const ENV_EXAMPLE_PATH = join(process.cwd(), ".env.local.example");

const REQUIRED_VARS: ReadonlyArray<string> = [
  "NEXT_PUBLIC_API_URL",
  "NEXT_PUBLIC_MAPBOX_TOKEN",
  "NEXT_PUBLIC_MAPBOX_STYLE_URL",
  "NEXT_PUBLIC_LAST_CALIBRATED",
  "NEXT_PUBLIC_SITE_URL",
];

describe("frontend/.env.local.example — submission deploy contract", () => {
  const env = readFileSync(ENV_EXAMPLE_PATH, "utf8");

  it.each(REQUIRED_VARS)("declares %s", (key) => {
    // Match the variable as a key (start of line OR after a comment block),
    // tolerant of `=` with optional value and trailing comment.
    const re = new RegExp(`(^|\\n)\\s*${key}\\s*=`);
    expect(env).toMatch(re);
  });

  it("documents the Mapbox token as REQUIRED for the Wall", () => {
    // Brief says: "When unset, W2's WallContainer falls back to a static
    // branded placeholder". The example MUST keep that prose so deployers
    // do not assume it is optional.
    expect(env).toMatch(/Mapbox/i);
    expect(env).toMatch(/access[- ]?token|access tokens|public token/i);
  });

  it("uses a `pk.` placeholder for the Mapbox token (signals the format)", () => {
    expect(env).toMatch(/NEXT_PUBLIC_MAPBOX_TOKEN\s*=\s*pk\./);
  });

  it("uses a `mapbox://styles/` placeholder for the custom style URL", () => {
    expect(env).toMatch(
      /NEXT_PUBLIC_MAPBOX_STYLE_URL\s*=\s*mapbox:\/\/styles\//,
    );
  });
});
