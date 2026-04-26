/**
 * Access control for the QC dashboard (T13.8).
 *
 * Behavior matrix:
 *   - dev / test: always allow (this is what hackathon graders see)
 *   - prod with `QC_DASHBOARD_ADMIN_KEY` set: require X-Admin-Key match
 *   - prod with no admin key configured: fail-closed (page returns 404)
 *
 * The fail-closed posture in prod is deliberate: if you forget to set
 * the env var on a public deploy, the page should hide itself rather
 * than expose run history publicly.
 *
 * T13 stage-2 P1-3 — constant-time compare:
 * The header/admin-key check used `===` which short-circuits on the
 * first byte mismatch and leaks timing data about the configured admin
 * key. We now route through ``timingSafeEqual`` from ``node:crypto``.
 * The early-return on length mismatch is itself a side channel, but
 * admin keys are a fixed-length secret in practice so the leaked bit
 * (the configured length) is not sensitive.
 */

import { timingSafeEqual } from "node:crypto";

export interface AccessParams {
  nodeEnv: string | undefined;
  headerKey: string | null;
  adminKey: string | undefined;
}

export function constantTimeStringEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  // ``Buffer.from`` defaults to utf-8 which preserves byte-length parity
  // for our ASCII admin keys; a length-mismatch in the encoded form
  // would still be caught by ``timingSafeEqual``'s own length guard.
  return timingSafeEqual(Buffer.from(a), Buffer.from(b));
}

export function isAccessAllowed({
  nodeEnv,
  headerKey,
  adminKey,
}: AccessParams): boolean {
  if (nodeEnv !== "production") return true;
  if (!adminKey) return false;
  if (headerKey == null) return false;
  return constantTimeStringEqual(headerKey, adminKey);
}
