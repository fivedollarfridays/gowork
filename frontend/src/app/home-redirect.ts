"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

/**
 * Returns true when the user has completed an assessment — i.e. their
 * session exists AND a feedback token for that session is in sessionStorage.
 *
 * Signal rationale: assess/page.tsx writes ``feedback_token_{session_id}``
 * to sessionStorage on successful submission (see T12.26 notes). There is
 * no separate ``assessment_complete`` flag; token presence is the closest
 * proxy without a round-trip to the backend.
 *
 * Returns ``false`` during SSR and on first render (before useEffect fires)
 * so the home content renders normally for everyone. After mount, if the
 * signal is present the caller's useEffect redirects to /daily.
 */
export function useAssessmentComplete(): boolean {
  const searchParams = useSearchParams();
  const sessionFromUrl = searchParams.get("session");
  const tokenFromUrl = searchParams.get("token");
  const [complete, setComplete] = useState(false);

  useEffect(() => {
    // URL presence is a strong signal: caller arrived with a session+token.
    if (sessionFromUrl && tokenFromUrl) {
      setComplete(true);
      return;
    }
    let sessionId: string | null = sessionFromUrl;
    if (!sessionId) {
      try {
        sessionId = sessionStorage.getItem("montgowork_session_id");
      } catch {
        sessionId = null;
      }
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
  }, [sessionFromUrl, tokenFromUrl]);

  return complete;
}
