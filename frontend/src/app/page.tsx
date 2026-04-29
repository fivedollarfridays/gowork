"use client";

/**
 * Home page — sprint/gowork-facelift Driver D (Phase D3).
 *
 * The 8-chapter scrollytelling homepage replaces the legacy 10-chapter
 * Wall (preserved on `archive/pre-gowork-facelift`). Returning users
 * with a completed assessment in sessionStorage skip the homepage and
 * route to `/daily`; first-time visitors see `<HomePage>`.
 *
 * The legacy hero/flow/stats landing remains preserved at `/archive`
 * for rollback insurance (T2.46).
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import HomePage from "@/components/home/HomePage";
import { useAssessmentComplete } from "./home-redirect";

export default function Home() {
  const router = useRouter();
  const assessmentComplete = useAssessmentComplete();

  useEffect(() => {
    if (assessmentComplete) {
      router.replace("/daily");
    }
  }, [assessmentComplete, router]);

  return <HomePage />;
}
