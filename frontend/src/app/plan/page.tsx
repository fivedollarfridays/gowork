"use client";

import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getPlan, generateNarrative } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { MondayMorning } from "@/components/plan/MondayMorning";
import { BarrierCardView } from "@/components/plan/BarrierCardView";
import { JobMatchCard } from "@/components/plan/JobMatchCard";
import { ComparisonView } from "@/components/plan/ComparisonView";
import { CreditResults } from "@/components/plan/CreditResults";
import { BarrierType, EmploymentStatus, AvailableHours } from "@/lib/types";
import type { CreditAssessmentResult, PlanNarrative, UserProfile } from "@/lib/types";
import { barrierCountToSeverity } from "@/lib/constants";

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
  };
}

function PlanSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-10 w-3/4 bg-muted rounded" />
      <div className="h-5 w-1/2 bg-muted rounded" />
      <div className="h-40 bg-muted rounded-xl" />
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="h-32 bg-muted rounded-xl" />
        <div className="h-32 bg-muted rounded-xl" />
      </div>
      <div className="h-48 bg-muted rounded-xl" />
    </div>
  );
}

function PlanContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session");
  const queryClient = useQueryClient();
  const [narrative, setNarrative] = useState<PlanNarrative | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["plan", sessionId],
    queryFn: () => getPlan(sessionId ?? ""),
    enabled: !!sessionId,
  });

  const handleNarrative = useCallback(
    () => generateNarrative(sessionId ?? ""),
    [sessionId],
  );
  const narrativeMutation = useMutation({
    mutationFn: handleNarrative,
    onSuccess: (result) => {
      setNarrative(result);
      queryClient.invalidateQueries({ queryKey: ["plan", sessionId] });
    },
  });

  const plan = data?.plan ?? null;

  // Load credit assessment from sessionStorage (set by assess page)
  const [creditResult] = useState<CreditAssessmentResult | null>(() => {
    if (!sessionId || typeof window === "undefined") return null;
    try {
      const stored = sessionStorage.getItem(`credit_${sessionId}`);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const profile = useMemo(
    () => data ? buildProfileFromPlan(data.session_id, data.barriers) : null,
    [data],
  );
  const planWithNarrative = useMemo(
    () => plan && narrative ? { ...plan, resident_summary: narrative.summary } : plan,
    [plan, narrative],
  );

  const { jobsNow, jobsAfter } = useMemo(() => {
    if (!plan) return { jobsNow: [], jobsAfter: [] };
    return {
      jobsNow: plan.job_matches.filter((j) => j.eligible_now),
      jobsAfter: plan.job_matches.filter((j) => !j.eligible_now),
    };
  }, [plan]);

  // Auto-generate narrative when plan loads (once)
  const narrativeTriggered = useRef(false);
  useEffect(() => {
    if (plan && !plan.resident_summary && !narrative && !narrativeTriggered.current) {
      narrativeTriggered.current = true;
      narrativeMutation.mutate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plan, narrative]);

  if (!sessionId) {
    return (
      <div className="text-center py-12 space-y-3">
        <p className="text-muted-foreground">No session ID provided.</p>
        <Button asChild variant="outline">
          <a href="/assess">Start an assessment</a>
        </Button>
      </div>
    );
  }

  if (isLoading) return <PlanSkeleton />;

  if (error) {
    return (
      <div className="text-center py-12 space-y-3">
        <p className="text-destructive">
          {(() => {
            const msg = error instanceof Error ? error.message : String(error);
            return msg.includes("404")
              ? "Session not found. It may have expired."
              : `Error: ${msg}`;
          })()}
        </p>
        <Button asChild variant="outline">
          <a href="/assess">Start a new assessment</a>
        </Button>
      </div>
    );
  }

  if (!data || !plan || !profile || !planWithNarrative) return null;

  return (
    <div className="space-y-10">
      {/* Monday Morning hero */}
      <MondayMorning
        plan={planWithNarrative}
        profile={profile}
        narrative={narrative}
        narrativeLoading={narrativeMutation.isPending}
      />

      <Separator />

      {/* Barrier cards */}
      {plan.barriers.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-primary">Your Barriers</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {plan.barriers.map((barrier) => (
              <BarrierCardView key={barrier.type} barrier={barrier} />
            ))}
          </div>
        </section>
      )}

      {/* Credit results */}
      {creditResult && (
        <>
          <Separator />
          <section className="space-y-4">
            <h2 className="text-xl font-semibold text-primary">Credit Assessment</h2>
            <CreditResults result={creditResult} />
          </section>
        </>
      )}

      <Separator />

      {/* Job matches — split by eligibility when credit data exists */}
      {plan.job_matches.length > 0 && (
        <section className="space-y-4">
          {creditResult ? (
            <>
              {jobsNow.length > 0 && (
                <div className="space-y-3">
                  <h2 className="text-xl font-semibold text-primary">Qualified Now</h2>
                  <div className="grid gap-4 sm:grid-cols-2">
                    {jobsNow.map((job, i) => (
                      <JobMatchCard key={`now-${job.title}-${job.company}-${i}`} job={job} creditResult={creditResult} />
                    ))}
                  </div>
                </div>
              )}
              {jobsAfter.length > 0 && (
                <div className="space-y-3">
                  <h2 className="text-xl font-semibold text-amber-600">After Credit Repair</h2>
                  <p className="text-sm text-muted-foreground">
                    These jobs require a credit check. Follow your credit repair plan to become eligible.
                  </p>
                  <div className="grid gap-4 sm:grid-cols-2">
                    {jobsAfter.map((job, i) => (
                      <JobMatchCard key={`after-${job.title}-${job.company}-${i}`} job={job} creditResult={creditResult} />
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <>
              <h2 className="text-xl font-semibold text-primary">Matched Jobs</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                {plan.job_matches.map((job, i) => (
                  <JobMatchCard key={`job-${job.title}-${job.company}-${i}`} job={job} />
                ))}
              </div>
            </>
          )}
        </section>
      )}

      <Separator />

      {/* Comparison view */}
      <ComparisonView plan={plan} profile={profile} creditResult={creditResult} />

      {/* Narrative error */}
      {narrativeMutation.isError && (
        <p className="text-sm text-destructive text-center">
          Failed to generate summary: {narrativeMutation.error.message}
        </p>
      )}
    </div>
  );
}

export default function PlanPage() {
  return (
    <main className="min-h-screen px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-3xl">
        <Suspense fallback={<PlanSkeleton />}>
          <PlanContent />
        </Suspense>
      </div>
    </main>
  );
}
