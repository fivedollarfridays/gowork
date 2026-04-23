"use client";

import { useEffect, useState } from "react";

/**
 * Returns true when the user has completed an assessment — i.e. their
 * session exists in sessionStorage AND a feedback token for that session
 * is present.
 *
 * Signal rationale: assess/page.tsx writes ``feedback_token_{session_id}``
 * to sessionStorage on successful submission (see T12.26 notes). There is
 * no separate ``assessment_complete`` flag; token presence is the closest
 * proxy without a round-trip to the backend.
 *
 * Implementation note: intentionally does NOT read from URL search params.
 * Using ``useSearchParams`` forces the page into dynamic rendering and
 * surfaces pre-existing SSR/prerender issues; sessionStorage alone is a
 * reliable post-mount signal for the redirect decision.
 *
 * Returns ``false`` during SSR and on first render (before useEffect fires)
 * so the home content renders normally for everyone. After mount, if the
 * signal is present the caller's useEffect redirects to /daily.
 */
export function useAssessmentComplete(): boolean {
  const [complete, setComplete] = useState(false);

  useEffect(() => {
    let sessionId: string | null;
    try {
      sessionId = sessionStorage.getItem("montgowork_session_id");
    } catch {
      sessionId = null;
    }
    if (!sessionId) {
      setComplete(false);
      return;
    }
    try {
      const token = sessionStorage.getItem(`feedback_token_${sessionId}`);
      setComplete(Boolean(token));
    } catch {
      setComplete(false);
    }
  }, []);

  return complete;
}
