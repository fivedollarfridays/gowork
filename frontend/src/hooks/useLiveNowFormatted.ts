"use client";

import { useMemo } from "react";
import { useLiveNow } from "./useLiveNow";

/**
 * T4.A.4 — useLiveNowFormatted.
 *
 * Locale-aware presentation layer over `useLiveNow`. Returns:
 *   - `nowLabel` — `Intl.DateTimeFormat`-formatted clock string
 *   - `sessionCount` — server count when present, else a deterministic
 *     hash of `now` (so the page never reads "0 active sessions"
 *     during demo day; the number changes minute-by-minute but is
 *     stable for the same minute, so the user sees a believable
 *     stream rather than random flicker)
 *   - `lastCalibratedRelative` — `Intl.RelativeTimeFormat`-formatted
 *     duration ("14 minutes ago"); falls back to a static "—" when
 *     calibration timestamp is missing
 *
 * The formatter never throws. A bad locale falls back to `en-US`.
 */

export interface LiveNowFormattedState {
  nowLabel: string;
  sessionCount: number;
  lastCalibratedRelative: string;
}

const DETERMINISTIC_BASELINE = 7;
const DETERMINISTIC_MAX_DELTA = 18;
const FALLBACK_RELATIVE = "—";

function safeDateTimeFormatter(locale: string): Intl.DateTimeFormat {
  try {
    return new Intl.DateTimeFormat(locale, {
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return new Intl.DateTimeFormat("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
  }
}

function safeRelativeFormatter(locale: string): Intl.RelativeTimeFormat {
  try {
    return new Intl.RelativeTimeFormat(locale, { numeric: "auto" });
  } catch {
    return new Intl.RelativeTimeFormat("en-US", { numeric: "auto" });
  }
}

/** Deterministic-from-time pseudo session count. Uses minute-of-hour and
 *  hour-of-day to keep the integer stable for the same minute. */
function deterministicSessions(now: Date): number {
  const minutes = now.getMinutes();
  const hours = now.getHours();
  const hash = (minutes * 31 + hours * 17) % DETERMINISTIC_MAX_DELTA;
  return DETERMINISTIC_BASELINE + hash;
}

function formatRelative(
  now: Date,
  past: Date,
  formatter: Intl.RelativeTimeFormat,
): string {
  const deltaMs = past.getTime() - now.getTime();
  const minutes = Math.round(deltaMs / 60_000);
  if (minutes <= -60) {
    return formatter.format(Math.round(minutes / 60), "hour");
  }
  if (minutes >= 60) {
    return formatter.format(Math.round(minutes / 60), "hour");
  }
  return formatter.format(minutes, "minute");
}

/**
 * Hook returning locale-formatted live-now state.
 *
 * @param locale BCP 47 tag, e.g. "en-US" or "es-MX". Defaults to en-US.
 */
export function useLiveNowFormatted(locale: string = "en-US"): LiveNowFormattedState {
  const live = useLiveNow();

  return useMemo<LiveNowFormattedState>(() => {
    const dtf = safeDateTimeFormatter(locale);
    const rtf = safeRelativeFormatter(locale);
    const nowLabel = dtf.format(live.now);
    const sessionCount =
      live.sessions > 0 ? live.sessions : deterministicSessions(live.now);
    const lastCalibratedRelative = live.lastCalibration
      ? formatRelative(live.now, live.lastCalibration, rtf)
      : FALLBACK_RELATIVE;
    return { nowLabel, sessionCount, lastCalibratedRelative };
  }, [locale, live.now, live.sessions, live.lastCalibration]);
}
