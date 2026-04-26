/**
 * Typed API client for the MontGoWork Appointments feature.
 *
 * All endpoints accept a `token` query parameter for auth. The backend
 * validates the token against the session referenced by `session_id`.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type AppointmentStatus =
  | "scheduled"
  | "attended"
  | "missed"
  | "cancelled"
  | "rescheduled";

export type AppointmentSource = "user" | "pathway_auto";

export interface Appointment {
  id: number;
  session_id: string;
  type: string;
  title: string;
  starts_at: string | null;
  ends_at: string | null;
  location_name: string | null;
  location_address: string | null;
  barrier_link: string | null;
  status: AppointmentStatus;
  source: AppointmentSource;
  notes: string | null;
}

/**
 * Per-request hard timeout (T13.92). Surfaces an AbortError to the
 * caller if the backend stops responding instead of letting the fetch
 * hang indefinitely.
 */
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

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: HeadersInit = { ...(init?.headers ?? {}) };
  if (init?.body) {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
  }
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers,
      signal: _composeSignal(init?.signal, controller.signal),
    });
    if (!res.ok) {
      const body = await res
        .json()
        .catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail || `API error ${res.status}`);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timeoutId);
  }
}

function qs(params: Record<string, string | number>): string {
  const search = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) search.set(k, String(v));
  return search.toString();
}

export function listAppointments(
  sessionId: string,
  token: string,
): Promise<Appointment[]> {
  return apiFetch(
    `/api/appointments?${qs({ session_id: sessionId, token })}`,
  );
}

export function listUpcoming(
  sessionId: string,
  days: number,
  token: string,
): Promise<Appointment[]> {
  return apiFetch(
    `/api/appointments/upcoming?${qs({
      session_id: sessionId,
      days,
      token,
    })}`,
  );
}

export function createAppointment(
  payload: Partial<Appointment> & { session_id: string; type: string; title: string },
  token: string,
): Promise<Appointment> {
  return apiFetch(`/api/appointments?${qs({ token })}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAppointment(
  id: number,
  changes: Partial<Appointment>,
  token: string,
): Promise<Appointment> {
  return apiFetch(`/api/appointments/${id}?${qs({ token })}`, {
    method: "PATCH",
    body: JSON.stringify(changes),
  });
}

export function markAttended(id: number, token: string): Promise<Appointment> {
  return apiFetch(`/api/appointments/${id}/attended?${qs({ token })}`, {
    method: "POST",
  });
}

export function markMissed(id: number, token: string): Promise<Appointment> {
  return apiFetch(`/api/appointments/${id}/missed?${qs({ token })}`, {
    method: "POST",
  });
}

export function cancelAppointment(
  id: number,
  token: string,
): Promise<Appointment> {
  return apiFetch(`/api/appointments/${id}?${qs({ token })}`, {
    method: "DELETE",
  });
}

export function fromPathway(
  sessionId: string,
  token: string,
): Promise<Appointment[]> {
  return apiFetch(
    `/api/appointments/from-pathway?${qs({
      session_id: sessionId,
      token,
    })}`,
    { method: "POST" },
  );
}
