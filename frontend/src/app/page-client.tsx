"use client";

/**
 * Home page client island (polish-2 T51 split).
 *
 * The server `page.tsx` renders this island after deciding on the
 * chapter-specific metadata. Returning users (with a completed
 * assessment in sessionStorage) are redirected to `/daily`; first-time
 * visitors get the 8-chapter `<HomePage>` shell.
 */
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import HomePage from "@/components/home/HomePage";
import { useAssessmentComplete } from "./home-redirect";

export default function HomeClient() {
  const router = useRouter();
  const assessmentComplete = useAssessmentComplete();

  useEffect(() => {
    if (assessmentComplete) {
      router.replace("/daily");
    }
  }, [assessmentComplete, router]);

  return <HomePage />;
}
