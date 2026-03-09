"use client";

import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getPlan, toggleAction } from "@/lib/api";
import { useClientStorage, useSessionId, useToken } from "./hooks";
import { useReducedMotion } from "framer-motion";
import { ScrollReveal } from "@/lib/motion";
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
import { ActionTimeline } from "@/components/plan/ActionTimeline";
import { ProgressSummary } from "@/components/plan/ProgressSummary";
import { CareerCenterExport } from "@/components/plan/CareerCenterExport";
import { EmailExport } from "@/components/plan/EmailExport";
import { PlanExport } from "@/components/plan/PlanExport";
import { EmptyState } from "@/components/EmptyState";
import { BarrierIntelChat } from "@/components/barrier-intel/BarrierIntelChat";
import { PlanTransition } from "@/components/plan/PlanTransition";
import { PlanSkeleton } from "@/components/plan/PlanSkeleton";
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


function PlanContent() {
  const { id: sessionId, ready: sessionReady } = useSessionId();
  const { token, ready: tokenReady } = useToken(sessionId);

  const { data, isLoading, error } = useQuery({
    queryKey: ["plan", sessionId, token],
    queryFn: () => getPlan(sessionId ?? "", token ?? undefined),
    enabled: !!sessionId && !!token,
  });

  const plan = data?.plan ?? null;

  const [checklist, setChecklist] = useState<Record<string, boolean>>({});
  const checklistInitRef = useRef(false);
  useEffect(() => {
    if (data?.action_checklist && !checklistInitRef.current) {
      setChecklist(data.action_checklist);
      checklistInitRef.current = true;
    }
  }, [data?.action_checklist]);

  const prefersReduced = useReducedMotion();

  // --- Transition screen state ---
  const [transitionDone, setTransitionDone] = useState(false);
  const handleTransitionComplete = useCallback(() => {
    setTransitionDone(true);
    window.scrollTo(0, 0);
    // Fire confetti after transition reveals plan
    if (!prefersReduced) {
      setTimeout(() => {
        import("canvas-confetti").then((mod) => {
          mod.default({
            particleCount: 80, spread: 70, origin: { y: 0.6 },
            ticks: 300, gravity: 0.8, disableForReducedMotion: true,
            colors: ["#1e3a5f", "#2d9596", "#d4a843"],
          });
        }).catch(() => {});
      }, 300);
    }
  }, [prefersReduced]);

  // --- Phase completion confetti ---
  const completedPhasesRef = useRef<Set<string>>(new Set());

  const handleToggle = useCallback((key: string, completed: boolean) => {
    setChecklist((prev) => {
      const next = { ...prev, [key]: completed };

      // Check if any phase just became fully complete
      if (completed && plan?.action_plan && !prefersReduced) {
        for (const phase of plan.action_plan.phases) {
          if (completedPhasesRef.current.has(phase.phase_id)) continue;
          const allDone = phase.actions.every((_, i) => {
            const k = `${phase.phase_id}:${i}`;
            return k === key ? completed : next[k];
          });
          if (allDone && phase.actions.length > 0) {
            completedPhasesRef.current.add(phase.phase_id);
            import("canvas-confetti").then((mod) => {
              mod.default({
                particleCount: 50, spread: 60, origin: { y: 0.7 },
                ticks: 200, gravity: 0.9, disableForReducedMotion: true,
                colors: ["#1e3a5f", "#2d9596", "#d4a843"],
              });
            }).catch(() => {});
          }
        }
      }

      return next;
    });
    toggleAction(sessionId ?? "", key, completed, token ?? undefined).catch(() => {});
  }, [plan, prefersReduced, sessionId, token]);

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

  const storedZip = useClientStorage(sessionId ? `zip_${sessionId}` : null);
  const zipCode = storedZip.value ?? "";
  const storedEnrolled = useClientStorage(sessionId ? `enrolled_${sessionId}` : null);
  const enrolledPrograms = useMemo<string[]>(() => {
    if (!storedEnrolled.value) return [];
    try { return JSON.parse(storedEnrolled.value); } catch { return []; }
  }, [storedEnrolled.value]);

  // Skip transition for error/missing-session states
  useEffect(() => {
    if (!transitionDone && sessionReady && tokenReady && (!sessionId || !token || error)) {
      setTransitionDone(true);
    }
  }, [transitionDone, sessionReady, tokenReady, sessionId, token, error]);

  // Show transition screen while loading or until transition completes
  if (!transitionDone) {
    return <PlanTransition dataReady={!!data} onComplete={handleTransitionComplete} />;
  }

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
    <div className="space-y-6">
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

      {/* Action Timeline */}
      {plan.action_plan && (
        <ScrollReveal>
          <div className="space-y-3">
            <ProgressSummary
              completed={Object.values(checklist).filter(Boolean).length}
              total={plan.action_plan.total_actions}
            />
            <ActionTimeline
              actionPlan={plan.action_plan}
              checklist={checklist}
              onToggle={handleToggle}
            />
          </div>
        </ScrollReveal>
      )}

      <Separator />

      {/* Job matches — unified ranked list with pagination */}
      <ScrollReveal>
      <section id="matched-jobs" className="space-y-3 scroll-mt-8">
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
          <BenefitsEligibility eligibility={plan.benefits_eligibility} enrolledPrograms={enrolledPrograms} />
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
    <div className="flex min-h-[100dvh] overscroll-none">
      <main className="flex-1 px-4 pt-8 pb-6 sm:px-8">
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
