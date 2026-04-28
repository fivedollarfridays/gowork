"use client";

/**
 * T2.47 — Home page (post-W2 rewrite).
 *
 * Replaces the legacy hero/flow/stats landing with The Wall. The legacy
 * landing is preserved at `/archive` (T2.46) for rollback insurance.
 *
 * Returning users (with a completed assessment in sessionStorage) skip
 * the Wall and go straight to `/daily`. First-time visitors see The Wall
 * — Carlos's story rendered as a Mapbox-driven scrollytelling.
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import WallContainer from "@/components/wall/WallContainer";
import { useAssessmentComplete } from "./home-redirect";

export default function Home() {
  const router = useRouter();
  const assessmentComplete = useAssessmentComplete();

  useEffect(() => {
    if (assessmentComplete) {
      router.replace("/daily");
    }
  }, [assessmentComplete, router]);

  return <WallContainer />;
}
