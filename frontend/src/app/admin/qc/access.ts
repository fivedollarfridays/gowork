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
 */

export interface AccessParams {
  nodeEnv: string | undefined;
  headerKey: string | null;
  adminKey: string | undefined;
}

export function isAccessAllowed({
  nodeEnv,
  headerKey,
  adminKey,
}: AccessParams): boolean {
  if (nodeEnv !== "production") return true;
  if (!adminKey) return false;
  return headerKey === adminKey;
}
