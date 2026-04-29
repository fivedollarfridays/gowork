#!/usr/bin/env node
/**
 * W5 Driver C — Spotlight invention #2: post-deploy-smoke.mjs
 *
 * Hits the production URL and asserts the canonical responses we
 * promise judges and social crawlers. One command, deterministic.
 *
 * Invocation:
 *   SITE_URL=https://gowork.vercel.app node scripts/post-deploy-smoke.mjs
 *   # or via npm:
 *   SITE_URL=https://gowork.vercel.app npm run post-deploy-smoke
 *
 * Default SITE_URL: https://gowork.vercel.app (W5 backlog default).
 *
 * Checks:
 *   1. GET /                  → 200 OK, text/html, contains GoWork hero string
 *   2. GET /api/og/1          → 200 OK, image/png
 *   3. GET /api/og/default    → 200 OK, image/png
 *   4. GET /bogus-url-xyz-w5c → 404, wall-metaphor copy in body
 *
 * Exits 0 iff all 4 checks pass. On any failure, prints a red banner
 * and exits non-zero with the count of failed checks.
 *
 * Honest uncertainty: this script does NOT scroll-and-render — it
 * makes raw HTTP calls. The cross-browser plan
 * (`docs/cross-browser-test-plan.md`) covers visual / interactive
 * assertions a human eyeball must verify.
 */
import process from "node:process";

const SITE_URL =
  process.env.SITE_URL ??
  process.env.NEXT_PUBLIC_SITE_URL ??
  "https://gowork.vercel.app";

const TIMEOUT_MS = 15_000;

/** A single check description. */
const CHECKS = [
  {
    label: "Home page (/)",
    path: "/",
    expectStatus: 200,
    expectContentType: /text\/html/,
    expectBodyMatch: /GoWork|wall|standing between you and a job/i,
  },
  {
    label: "OG card chapter 1 (/api/og/1)",
    path: "/api/og/1",
    expectStatus: 200,
    expectContentType: /image\/png/,
  },
  {
    label: "OG default fallback (/api/og/default)",
    path: "/api/og/default",
    expectStatus: 200,
    expectContentType: /image\/png/,
  },
  {
    label: "404 wall-metaphor (/bogus-url-xyz-w5c)",
    path: "/bogus-url-xyz-w5c",
    expectStatus: 404,
    // The wall-metaphor copy is the W4-B sentinel string; loose match.
    expectBodyMatch: /wall|404|través del muro|path to this URL/i,
  },
];

function banner(msg, char = "=") {
  const line = char.repeat(72);
  console.log(`\n${line}\n${msg}\n${line}`);
}

async function runCheck(check) {
  const url = `${SITE_URL}${check.path}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(timer);
    const failures = [];

    if (res.status !== check.expectStatus) {
      failures.push(`expected status ${check.expectStatus}, got ${res.status}`);
    }
    const ct = res.headers.get("content-type") ?? "";
    if (check.expectContentType && !check.expectContentType.test(ct)) {
      failures.push(
        `expected content-type ${check.expectContentType}, got '${ct}'`,
      );
    }
    if (check.expectBodyMatch) {
      // Read body as text. PNGs become gibberish but the regex is for HTML.
      const body = await res.text();
      if (!check.expectBodyMatch.test(body)) {
        failures.push(
          `body did not match ${check.expectBodyMatch} (first 240 chars: ${body.slice(0, 240)})`,
        );
      }
    }

    if (failures.length > 0) {
      banner(`✗ ${check.label} (${url})\n  ${failures.join("\n  ")}`, "!");
      return false;
    }
    banner(`✓ ${check.label} (${url}) — ok`, "-");
    return true;
  } catch (err) {
    clearTimeout(timer);
    banner(`✗ ${check.label} (${url}) — fetch error: ${err.message}`, "!");
    return false;
  }
}

async function main() {
  banner(`GoWork post-deploy smoke — SITE_URL=${SITE_URL}`);
  let failures = 0;
  for (const check of CHECKS) {
    const ok = await runCheck(check);
    if (!ok) failures++;
  }
  if (failures > 0) {
    banner(`STOP: ${failures} of ${CHECKS.length} checks failed.`, "X");
    process.exit(failures);
  }
  banner(`ALL ${CHECKS.length} CHECKS GREEN — production is live and well.`);
  process.exit(0);
}

main();
