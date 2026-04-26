/**
 * Typed API client for the advisor inbox (T12.31).
 *
 * Every endpoint below is gated by the advisor's ``X-Admin-Key`` token
 * (see ``docs/security/advisor-auth.md``). The token is city-scoped on
 * the server — the UI does not encode city; the backend derives it
 * from the token. Cross-city access returns HTTP 403.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type AdvisorStallLevel = "soft" | "medium" | "hard";

export interface AdvisorStalledSession {
  session_id: string;
  city: string;
  stall_level: AdvisorStallLevel;
  days_stalled: number;
}

export interface StalledSessionsResponse {
  sessions: AdvisorStalledSession[];
}

export interface AdvisorSessionDetail {
  session_id: string;
  city: string;
  stall_level: AdvisorStallLevel | "none";
  days_stalled: number;
}

export interface SendNoteResult {
  success: boolean;
  skipped_reason: string | null;
  message_id: string | null;
}

export class AdvisorApiError extends Error {
  public readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "AdvisorApiError";
  }
}

async function readDetail(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: string };
    return body?.detail || `API error ${res.status}`;
  } catch {
    return `API error ${res.status}`;
  }
}

/** Per-request hard timeout (T13.92). */
const REQUEST_TIMEOUT_MS = 30_000;

/**
 * Compose the caller's signal (if any) with our local timeout signal so
 * that BOTH abort triggers are honoured (T13 stage-2 P1-4). The prior
 * ``init?.signal ?? controller.signal`` silently dropped the timeout
 * whenever the caller supplied their own signal.
 */
function _composeSignal(
  callerSignal: AbortSignal | null | undefined,
  timeoutSignal: AbortSignal,
): AbortSignal {
  if (!callerSignal) return timeoutSignal;
  return AbortSignal.any([callerSignal, timeoutSignal]);
}

async function advisorFetch<T>(
  path: string,
  token: string,
  init?: RequestInit,
): Promise<T> {
  const headers: Record<string, string> = {
    "X-Admin-Key": token,
    ...((init?.headers as Record<string, string>) ?? {}),
  };
  if (init?.body) headers["Content-Type"] = "application/json";
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers,
      signal: _composeSignal(init?.signal, controller.signal),
    });
    if (!res.ok) {
      throw new AdvisorApiError(res.status, await readDetail(res));
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timeoutId);
  }
}

export function listStalledSessions(
  token: string,
): Promise<StalledSessionsResponse> {
  return advisorFetch<StalledSessionsResponse>(
    "/api/advisor/stalled-sessions",
    token,
  );
}

export function getSessionDetail(
  sessionId: string,
  token: string,
): Promise<AdvisorSessionDetail> {
  return advisorFetch<AdvisorSessionDetail>(
    `/api/advisor/sessions/${encodeURIComponent(sessionId)}`,
    token,
  );
}

export function sendAdvisorNote(
  sessionId: string,
  message: string,
  token: string,
): Promise<SendNoteResult> {
  return advisorFetch<SendNoteResult>(
    `/api/advisor/sessions/${encodeURIComponent(sessionId)}/note`,
    token,
    { method: "POST", body: JSON.stringify({ message }) },
  );
}
