/**
 * Error reporter (T1.117).
 *
 * Module-level singleton with a single `report(error, context?)` API.
 *
 * - Dev: `console.error` with the full scrubbed payload.
 * - Production: posts to `/api/errors/ingest` (W4 endpoint). Failures
 *   are silently swallowed — we never want the reporter to itself
 *   throw and crash the page.
 *
 * PII contract:
 *   - context values matching email regex → replaced with `<EMAIL>`
 *   - stack trace path components matching `/Users/<name>` or
 *     `C:\Users\<name>` → replaced with `<USER>`
 */

const ENDPOINT = "/api/errors/ingest";
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/i;

type ContextValue = string | number;
type Context = Record<string, ContextValue>;

interface ReportPayload {
  message: string;
  name: string;
  stack: string;
  context: Context;
  timestamp: number;
}

let inProduction: boolean | null = null;
function isProduction(): boolean {
  if (inProduction !== null) return inProduction;
  inProduction = process.env.NODE_ENV === "production";
  return inProduction;
}

/** Scrub PII from a context dictionary. Pure function. */
export function scrubContext(input: Context | undefined): Context {
  if (!input) return {};
  const out: Context = {};
  for (const [k, v] of Object.entries(input)) {
    if (typeof v === "number") {
      out[k] = v;
      continue;
    }
    out[k] = EMAIL_RE.test(v) ? "<EMAIL>" : v;
  }
  return out;
}

/** Scrub PII from a stack trace string. Pure function. */
export function scrubStackTrace(stack: string | undefined): string {
  if (!stack) return "";
  return stack
    .replace(/\/Users\/[^/\s)]+/gi, "/Users/<USER>")
    .replace(/[Cc]:\\Users\\[^\\\s)]+/g, "C:\\Users\\<USER>");
}

function buildPayload(error: Error, context?: Context): ReportPayload {
  return {
    message: error.message,
    name: error.name,
    stack: scrubStackTrace(error.stack),
    context: scrubContext(context),
    timestamp: Date.now(),
  };
}

async function sendToBackend(payload: ReportPayload): Promise<void> {
  if (typeof fetch !== "function") return;
  try {
    await fetch(ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      keepalive: true,
    });
  } catch {
    /* swallow — reporter MUST NOT throw */
  }
}

/**
 * Report an error.
 *
 * Always safe to call — never throws. In dev, logs to console; in
 * production, posts to the backend ingest endpoint (silently no-ops
 * if the endpoint is missing).
 */
export function report(error: Error, context?: Context): void {
  const payload = buildPayload(error, context);
  if (isProduction()) {
    void sendToBackend(payload);
    return;
  }
  // Dev path — console.error in a way that's easy to spot in DevTools.
  // eslint-disable-next-line no-console
  console.error("[gowork:error]", payload);
}

/** Reset cached production flag — for tests only. */
export function _resetReporterForTests(): void {
  inProduction = null;
}
