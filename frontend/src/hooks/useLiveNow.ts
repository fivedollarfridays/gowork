"use client";

import { useQuery } from "@tanstack/react-query";

const POLL_MS = 10_000;
const DEFAULT_ENDPOINT = "/api/now";

export interface LiveNowState {
  now: Date;
  sessions: number;
  lastCalibration: Date | null;
}

interface LiveNowPayload {
  now?: string | number;
  sessions?: number;
  lastCalibration?: string | number | null;
}

const FALLBACK_PAYLOAD: LiveNowState = {
  now: new Date(0),
  sessions: 0,
  lastCalibration: null,
};

function clientFallback(): LiveNowState {
  return {
    now: typeof window === "undefined" ? new Date(0) : new Date(),
    sessions: 0,
    lastCalibration: null,
  };
}

function parseDate(value: string | number | null | undefined): Date | null {
  if (value === null || value === undefined) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

async function fetchLiveNow(endpoint: string): Promise<LiveNowState> {
  try {
    const res = await fetch(endpoint, { cache: "no-store" });
    if (!res.ok) return clientFallback();
    const body = (await res.json()) as LiveNowPayload;
    const now = parseDate(body.now) ?? new Date();
    return {
      now,
      sessions: typeof body.sessions === "number" ? body.sessions : 0,
      lastCalibration: parseDate(body.lastCalibration),
    };
  } catch {
    return clientFallback();
  }
}

/**
 * Live "as of right now" telemetry.
 *
 * Polls `/api/now` every 10 seconds via `@tanstack/react-query`. If the
 * endpoint returns 404 or rejects (W4 hasn't built it yet), we degrade
 * gracefully to client-computed `new Date()` and zeroed counters — the
 * page never blocks on a missing backend.
 *
 * SSR-safe: returns `new Date(0)` placeholder during server render
 * (avoids hydration mismatch for time-sensitive UI).
 */
export function useLiveNow(endpoint: string = DEFAULT_ENDPOINT): LiveNowState {
  const { data } = useQuery({
    queryKey: ["live-now", endpoint],
    queryFn: () => fetchLiveNow(endpoint),
    refetchInterval: POLL_MS,
    refetchOnWindowFocus: false,
    // Stale immediately so the first fetch always runs.
    staleTime: 0,
    placeholderData:
      typeof window === "undefined" ? FALLBACK_PAYLOAD : clientFallback(),
  });
  return data ?? FALLBACK_PAYLOAD;
}
