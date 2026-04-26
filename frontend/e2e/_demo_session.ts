/**
 * Shared demo-session credentials for the @critical Playwright suite.
 *
 * The MontGoWork demo seed (`backend/app/demo_seed_s12b.py` + S13 QC
 * extension `_demo_seed_qc.py`) deterministically derives every session
 * id and feedback-token plaintext from a SHA256 of stable labels. We
 * inline the resulting values so the specs can run against a freshly
 * reset DB (`python scripts/qc_reset.py`) without round-tripping through
 * sqlite at test time.
 *
 * Token shapes:
 *   - session id:  uuid4 from sha256("s12b-demo:<city>:<state>")[:16]
 *   - feedback:    "demo-feedback-active-" + sha256("qc:<sid>:feedback-active")[:24]
 *   - advisor:     "mw_adv_demo_<city>_" + sha256("qc-advisor:<city>")[:24]
 *
 * If you change the seed-derivation in those Python modules, regenerate
 * these constants — they are the authoritative match.
 */
export const DEMO = {
  // Worker session: Montgomery medium stall (Beat 2/3/4 demo target).
  workerMontgomeryMedium: {
    sessionId: "f888fa8b-c8ae-49e4-84fd-410751aaa697",
    feedbackToken: "demo-feedback-active-1945c3fc72c3c9489eeff3ed",
  },
  // Worker session: Montgomery hard stall (advisor inbox surfaces this).
  workerMontgomeryHard: {
    sessionId: "88aa2ba4-1d57-471d-9391-8b31abc0b5ec",
    feedbackToken: "demo-feedback-active-541ec0e8e1784695ae206a2c",
  },
  // Advisor token plaintext for the Montgomery scope.
  advisorMontgomery: {
    plaintext: "mw_adv_demo_montgomery_8cb557a4cfd01216d446f750",
    advisorId: "adv-demo-montgomery",
  },
} as const;

/** Build a `?session=<sid>&token=<tok>` query string for worker pages. */
export function workerAuthQuery(creds: {
  sessionId: string;
  feedbackToken: string;
}): string {
  return `session=${creds.sessionId}&token=${creds.feedbackToken}`;
}

/** API_BASE used by the backend; mirrors NEXT_PUBLIC_API_URL default. */
export const BACKEND_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Detect a live MontGoWork backend (vs. an unrelated app on the same port).
 *
 * The bare `/health` is shared by many FastAPI services; we probe `GET /`
 * which `app.main.py:root()` answers with the literal `"MontGoWork API"`
 * banner. Returns the skip-reason string when the backend is missing /
 * wrong, or `null` when it's healthy and ours.
 */
export async function detectBackend(
  request: { get: (url: string) => Promise<{ ok(): boolean; json(): Promise<unknown> }> },
): Promise<string | null> {
  let res: { ok(): boolean; json(): Promise<unknown> } | null = null;
  try {
    res = await request.get(`${BACKEND_BASE}/`);
  } catch {
    return `Cannot reach ${BACKEND_BASE}/ — start it with \`uvicorn app.main:app --port 8000\``;
  }
  if (!res.ok()) {
    return `${BACKEND_BASE}/ returned non-200 — backend down?`;
  }
  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    return `${BACKEND_BASE}/ did not return JSON — wrong service on port?`;
  }
  const message = (body as { message?: string }).message ?? "";
  if (!/MontGoWork/i.test(message)) {
    return `${BACKEND_BASE}/ is not the MontGoWork backend (got message=${JSON.stringify(message)})`;
  }
  return null;
}
