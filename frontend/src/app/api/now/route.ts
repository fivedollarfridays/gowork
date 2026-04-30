/**
 * GET /api/now — live "as of right now" telemetry endpoint.
 *
 * Polled every 10s by `useLiveNow` (and consumed by `<PageMeta />` LIVE
 * row + `<LiveNow />` widget). When the FastAPI backend exposes its own
 * `/now` endpoint we proxy through; otherwise we return a sensible stub
 * so the demo never shows zero sessions and the dev console doesn't 404
 * every 10 seconds.
 *
 * Stub payload mirrors the LiveNowPayload contract defined in
 * `src/hooks/useLiveNow.ts`.
 */

import { NextResponse } from "next/server";

const BACKEND_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? process.env.API_URL ?? "";

interface LiveNowPayload {
  now: string;
  sessions: number;
  lastCalibration: string | null;
}

function stubPayload(): LiveNowPayload {
  // Calibration jitters a few minutes back so the "calibrated 14m ago"
  // line in the HUD reads non-zero on a cold load.
  const now = new Date();
  const calibrated = new Date(now.getTime() - 14 * 60 * 1000);
  return {
    now: now.toISOString(),
    sessions: 6,
    lastCalibration: calibrated.toISOString(),
  };
}

async function tryBackendProxy(): Promise<LiveNowPayload | null> {
  if (!BACKEND_BASE) return null;
  try {
    const res = await fetch(`${BACKEND_BASE}/now`, {
      cache: "no-store",
      // 1s budget — if the backend is sluggish, fall back to the stub
      // rather than blocking the home page polling loop.
      signal: AbortSignal.timeout(1000),
    });
    if (!res.ok) return null;
    const body = (await res.json()) as Partial<LiveNowPayload>;
    return {
      now: typeof body.now === "string" ? body.now : new Date().toISOString(),
      sessions: typeof body.sessions === "number" ? body.sessions : 0,
      lastCalibration:
        typeof body.lastCalibration === "string" ? body.lastCalibration : null,
    };
  } catch {
    return null;
  }
}

export async function GET() {
  const payload = (await tryBackendProxy()) ?? stubPayload();
  return NextResponse.json(payload, {
    headers: { "Cache-Control": "no-store, max-age=0" },
  });
}
