"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getPlan } from "@/lib/api";
import { useReducedMotion } from "framer-motion";
import { ScrollReveal, ShimmerBar } from "@/lib/motion";
import { Clock, MapPin, Phone, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { MondayMorning } from "@/components/plan/MondayMorning";
import { BarrierCardView } from "@/components/plan/BarrierCardView";
import { JobListSection } from "@/components/plan/JobListSection";
import { ComparisonView } from "@/components/plan/ComparisonView";
import { CreditResults } from "@/components/plan/CreditResults";
import { JobReadinessResults } from "@/components/plan/JobReadinessResults";
import { BenefitsCliffChart } from "@/components/plan/BenefitsCliffChart";
import { BenefitsEligibility } from "@/components/plan/BenefitsEligibility";
import { CareerCenterExport } from "@/components/plan/CareerCenterExport";
import { EmailExport } from "@/components/plan/EmailExport";
import { PlanExport } from "@/components/plan/PlanExport";
import { EmptyState } from "@/components/EmptyState";
import { BarrierIntelChat } from "@/components/barrier-intel/BarrierIntelChat";
import { BarrierType, EmploymentStatus, AvailableHours } from "@/lib/types";
import type { CreditAssessmentResult, UserProfile } from "@/lib/types";
import { barrierCountToSeverity, CAREER_CENTER, mapsUrl, toTelHref } from "@/lib/constants";

const BARRIER_TYPE_VALUES = new Set<string>(Object.values(BarrierType));

function buildProfileFromPlan(sessionId: string, barriers: string[]): UserProfile {
  const validBarriers = barriers.filter((b): b is BarrierType => BARRIER_TYPE_VALUES.has(b));
  return {
    session_id: sessionId,
    zip_code: "",
    employment_status: EmploymentStatus.UNEMPLOYED,
    barrier_count: validBarriers.length,
    primary_barriers: validBarriers,
    barrier_severity: barrierCountToSeverity(validBarriers.length),
    needs_credit_assessment: validBarriers.includes(BarrierType.CREDIT),
    transit_dependent: validBarriers.includes(BarrierType.TRANSPORTATION),
    schedule_type: AvailableHours.DAYTIME,
    work_history: "",
    target_industries: [],
    record_profile: null,
  };
}


function PlanSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading your plan">
      <ShimmerBar height="2.5rem" width="75%" />
      <ShimmerBar height="1.25rem" width="50%" />
      <ShimmerBar height="10rem" />
      <div className="grid gap-4 sm:grid-cols-2">
        <ShimmerBar height="8rem" />
        <ShimmerBar height="8rem" />
      </div>
      <ShimmerBar height="12rem" />
    </div>
  );
}

function useClientStorage(key: string | null): { value: string | null; ready: boolean } {
  const [state, setState] = useState<{ value: string | null; ready: boolean }>({ value: null, ready: false });
  useEffect(() => {
    if (!key) { setState({ value: null, ready: true }); return; }
    try { setState({ value: sessionStorage.getItem(key), ready: true }); } catch { setState({ value: null, ready: true }); }
  }, [key]);
  return state;
}

function useSessionId(): { id: string | null; ready: boolean } {
  const searchParams = useSearchParams();
  const fromUrl = searchParams.get("session");
  const stored = useClientStorage(fromUrl ? null : "montgowork_session_id");

  useEffect(() => {
    if (fromUrl) {
      try { sessionStorage.setItem("montgowork_session_id", fromUrl); } catch {}
    }
  }, [fromUrl]);

  if (fromUrl) return { id: fromUrl, ready: true };
  return { id: stored.value, ready: stored.ready };
}

function useToken(sessionId: string | null): { token: string | null; ready: boolean } {
  const searchParams = useSearchParams();
  const fromUrl = searchParams.get("token");
  const storageKey = (!fromUrl && sessionId) ? `feedback_token_${sessionId}` : null;
  const stored = useClientStorage(storageKey);

  useEffect(() => {
    if (fromUrl && sessionId) {
      try { sessionStorage.setItem(`feedback_token_${sessionId}`, fromUrl); } catch {}
    }
  }, [fromUrl, sessionId]);

  if (fromUrl) return { token: fromUrl, ready: true };
  return { token: stored.value, ready: stored.ready };
}

function PlanContent() {
  const { id: sessionId, ready: sessionReady } = useSessionId();
  const { token, ready: tokenReady } = useToken(sessionId);

  const { data, isLoading, error } = useQuery({
    queryKey: ["plan", sessionId, token],
    queryFn: () => getPlan(sessionId ?? "", token ?? undefined),
    enabled: !!sessionId && !!token,
  });

  const plan = data?.plan ?? null;

  useEffect(() => {
    if (plan) window.scrollTo(0, 0);
  }, [plan]);

  // Load credit assessment: sessionStorage first (in-tab cache), backend fallback
  const storedCredit = useClientStorage(sessionId ? `credit_${sessionId}` : null);
  const localCredit = useMemo<CreditAssessmentResult | null>(() => {
    if (!storedCredit.value) return null;
    try { return JSON.parse(storedCredit.value); } catch { return null; }
  }, [storedCredit.value]);
  const creditResult = localCredit ?? data?.credit_profile ?? null;

  const profile = useMemo(
    () => data ? buildProfileFromPlan(data.session_id, data.barriers) : null,
    [data],
  );

  const zipCode = useMemo(() => {
    if (typeof window === "undefined" || !sessionId) return "";
    return sessionStorage.getItem(`zip_${sessionId}`) ?? "";
  }, [sessionId]);

  const prefersReduced = useReducedMotion();
  const hasFiredConfetti = useRef(false);
  useEffect(() => {
    if (data && !hasFiredConfetti.current && !prefersReduced) {
      hasFiredConfetti.current = true;
      import("canvas-confetti").then((mod) => {
        mod.default({
          particleCount: 60,
          spread: 50,
          origin: { y: 0.7 },
          disableForReducedMotion: true,
          colors: ["#1e3a5f", "#2d9596", "#d4a843"],
        });
      }).catch(() => {});
    }
  }, [data, prefersReduced]);

  if (!sessionReady || !tokenReady || isLoading) return <PlanSkeleton />;

  if (!sessionId || !token) {
    return (
      <div className="text-center py-12 space-y-3">
        <p className="text-muted-foreground">{!sessionId ? "No session ID provided." : "No access token found."}</p>
        <Button asChild variant="outline">
          <a href="/assess">Start an assessment</a>
        </Button>
      </div>
    );
  }

  if (error) {
    const msg = error instanceof Error ? error.message : String(error);
    const friendlyMessage = msg.includes("404")
      ? "Session not found. It may have expired."
      : "Something went wrong loading your plan. Please try again.";

    return (
      <div role="alert" className="text-center py-12 space-y-3">
        <p className="text-destructive">{friendlyMessage}</p>
        <Button asChild variant="outline">
          <a href="/assess">Start a new assessment</a>
        </Button>
      </div>
    );
  }

  if (!data || !plan || !profile) {
    return (
      <div role="alert" className="text-center py-12 space-y-3">
        <p className="text-destructive">Something went wrong loading your plan.</p>
        <Button asChild variant="outline">
          <a href="/assess">Start a new assessment</a>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {/* Monday Morning hero */}
      <ScrollReveal>
        <MondayMorning
          plan={plan}
          profile={profile}
          firstStepAction={
            <CareerCenterExport sessionId={sessionId} token={token ?? undefined} />
          }
        />
      </ScrollReveal>

      <Separator />

      {/* Job matches — unified ranked list with pagination */}
      <ScrollReveal>
      <section id="matched-jobs" className="space-y-6 scroll-mt-8">
        {(plan.job_matches?.length ?? 0) > 0 ? (
          <JobListSection
            jobs={plan.job_matches}
            creditResult={creditResult}
          />
        ) : (
          <EmptyState
            icon={Search}
            title="No job matches yet"
            description="We're still looking for the best matches for your profile. Check back soon or update your assessment."
            actionLabel="Update Assessment"
            actionHref="/assess"
          />
        )}
      </section>
      </ScrollReveal>

      {/* Benefits eligibility — programs user may qualify for */}
      {plan.benefits_eligibility && (
        <>
          <Separator />
          <BenefitsEligibility eligibility={plan.benefits_eligibility} />
        </>
      )}

      {/* Benefits cliff chart — only when cliff data exists */}
      {plan.benefits_cliff_analysis && (
        <>
          <Separator />
          <BenefitsCliffChart analysis={plan.benefits_cliff_analysis} />
        </>
      )}

      <Separator />

      {/* Comparison view */}
      <ScrollReveal>
        <ComparisonView plan={plan} profile={profile} creditResult={creditResult} />
      </ScrollReveal>

      {/* Barrier cards */}
      {plan.barriers.length > 0 && (
        <>
          <Separator />
          <ScrollReveal>
            <section className="space-y-4">
              <h2 className="text-xl font-semibold text-primary">Your Barriers</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                {plan.barriers.map((barrier) => (
                  <BarrierCardView key={barrier.type} barrier={barrier} sessionId={sessionId ?? undefined} token={token ?? undefined} zipCode={zipCode} />
                ))}
              </div>
            </section>
          </ScrollReveal>
        </>
      )}

      {/* Credit results */}
      {creditResult && (
        <>
          <Separator />
          <ScrollReveal>
            <section className="space-y-4">
              <h2 className="text-xl font-semibold text-primary">Credit Assessment</h2>
              <CreditResults result={creditResult} />
            </section>
          </ScrollReveal>
        </>
      )}

      {/* Job Readiness Score */}
      {plan.job_readiness && (
        <>
          <Separator />
          <ScrollReveal>
            <section className="space-y-4">
              <h2 className="text-xl font-semibold text-primary">Job Readiness</h2>
              <JobReadinessResults result={plan.job_readiness} />
            </section>
          </ScrollReveal>
        </>
      )}

      {/* What's Next CTA */}
      <Separator />
      <ScrollReveal>
      <Card className="border-secondary/30 bg-secondary/5">
        <CardHeader>
          <CardTitle className="text-xl">What&apos;s Next?</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <ol className="list-decimal list-inside space-y-3 text-sm">
            <li><strong>Download your Career Center Ready Package</strong> <span className="text-muted-foreground">using the button in Step 1 above.</span></li>
            <li><strong>Bring this plan to the Montgomery Career Center:</strong></li>
          </ol>
          <div className="ml-6 space-y-1.5 text-sm text-muted-foreground">
            <p className="flex items-center gap-2">
              <MapPin className="h-4 w-4 shrink-0" />
              <a
                href={mapsUrl(CAREER_CENTER.address)}
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-foreground transition-colors"
              >
                {CAREER_CENTER.address}
              </a>
            </p>
            <p className="flex items-center gap-2">
              <Phone className="h-4 w-4 shrink-0" />
              <a
                href={toTelHref(CAREER_CENTER.phone)}
                className="underline hover:text-foreground transition-colors"
              >
                {CAREER_CENTER.phone}
              </a>
            </p>
            <p className="flex items-center gap-2"><Clock className="h-4 w-4 shrink-0" /> {CAREER_CENTER.hours}</p>
          </div>
          <ol start={3} className="list-decimal list-inside space-y-3 text-sm">
            <li><strong>Ask for a case manager</strong> and show them your Career Center Ready Package.</li>
          </ol>
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <PlanExport plan={plan} creditResult={creditResult} feedbackToken={token} />
            <EmailExport sessionId={sessionId} token={token ?? undefined} />
            <Button asChild variant="outline" size="sm">
              <a href="/assess">Start New Assessment</a>
            </Button>
          </div>
        </CardContent>
      </Card>
      </ScrollReveal>

    </div>
  );
}

export default function PlanPage() {
  return (
    <div className="flex min-h-screen">
      <main className="flex-1 px-4 py-8 sm:px-8">
        <div className="mx-auto max-w-3xl">
          <Suspense fallback={<PlanSkeleton />}>
            <PlanContent />
          </Suspense>
        </div>
      </main>
      <Suspense fallback={null}>
        <PlanChatSidebar />
      </Suspense>
    </div>
  );
}

function PlanChatSidebar() {
  const { id: sessionId } = useSessionId();
  return <BarrierIntelChat sessionId={sessionId} />;
}
