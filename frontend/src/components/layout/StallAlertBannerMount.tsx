"use client";

import { useQuery } from "@tanstack/react-query";
import { useSessionId, useToken } from "@/app/plan/hooks";
import { previewDigest, type DigestResult } from "@/lib/api/digest";
import {
  StallAlertBanner,
  type StallLevel,
} from "@/components/StallAlertBanner";

/**
 * Site-wide mount for the stall alert banner. Queries the daily digest for
 * the current session and derives a `StallLevel` from the response.
 *
 * NOTE (T12.30): The digest preview endpoint currently returns
 * `section_counts.stall` as a count (non-zero whenever the session is in any
 * stall state — see `engagement/digest_sections.py::render_stall_alerts_section`).
 * The backend does not yet expose the raw `stall_level` via the preview
 * endpoint; until it does, we map any non-zero stall count to "hard" so the
 * banner fires on exactly the sessions the backend thinks need attention.
 * When T12.18 exposes `stall_level` in the preview response, swap the
 * derivation below to read it directly.
 */
export function StallAlertBannerMount() {
  const { id: sessionId, ready: sessionReady } = useSessionId();
  const { token, ready: tokenReady } = useToken(sessionId);

  const enabled = Boolean(sessionReady && tokenReady && sessionId && token);

  const digestQ = useQuery<DigestResult>({
    queryKey: ["digest-banner", sessionId, token],
    queryFn: () => previewDigest(sessionId!, token!),
    enabled,
    // Banner should not thrash on transient errors — don't retry aggressively.
    retry: 0,
    // Keep fresh for 5 minutes; this is a site-wide indicator, not a ticker.
    staleTime: 5 * 60 * 1000,
  });

  const stallLevel: StallLevel =
    digestQ.data && digestQ.data.section_counts.stall > 0 ? "hard" : "none";

  return <StallAlertBanner stallLevel={stallLevel} />;
}
