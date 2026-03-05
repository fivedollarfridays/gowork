"use client";

import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getPlan, generateNarrative, getJobs } from "@/lib/api";
import { Briefcase, ExternalLink, Loader2, Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { MondayMorning } from "@/components/plan/MondayMorning";
import { BarrierCardView } from "@/components/plan/BarrierCardView";
import { JobMatchCard } from "@/components/plan/JobMatchCard";
import { ComparisonView } from "@/components/plan/ComparisonView";
import { CreditResults } from "@/components/plan/CreditResults";
import { EmailExport } from "@/components/plan/EmailExport";
import { PlanExport } from "@/components/plan/PlanExport";
import { EmptyState } from "@/components/EmptyState";
import { BarrierType, EmploymentStatus, AvailableHours } from "@/lib/types";
import type { CreditAssessmentResult, EnrichedJob, PlanNarrative, UserProfile } from "@/lib/types";
import { barrierCountToSeverity, safeHref } from "@/lib/constants";

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

function LiveJobCard({ job }: { job: EnrichedJob }) {
  const href = job.url ? safeHref(job.url) : undefined;
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
            <Briefcase className="h-5 w-5 text-foreground/70" />
          </div>
          <div>
            <CardTitle className="text-base">{job.title}</CardTitle>
            {job.company && <p className="text-sm text-muted-foreground">{job.company}</p>}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-1.5">
          {job.industry && <Badge variant="secondary" className="text-xs">{job.industry}</Badge>}
          {job.credit_check_required === "yes" && (
            <Badge variant="outline" className="text-xs text-accent-foreground border-accent/30 bg-accent/10">Credit check required</Badge>
          )}
        </div>
        {href && (
          <Button variant="outline" size="sm" className="gap-1.5" asChild>
            <a href={href} target="_blank" rel="noopener noreferrer">
              Apply <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

function PlanSkeleton() {
  return (
    <div className="space-y-6 animate-pulse" aria-busy="true" aria-label="Loading your plan">
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

  const barriers = data?.barriers ?? [];
  const barrierParam = barriers.length > 0 ? barriers.join(",") : undefined;

  const { data: liveJobs, isLoading: liveJobsLoading } = useQuery({
    queryKey: ["liveJobs", barrierParam],
    queryFn: () => getJobs({ barriers: barrierParam }),
    enabled: !!data,
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

  if (!data || !plan || !profile || !planWithNarrative) {
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
      <MondayMorning
        plan={planWithNarrative}
        profile={profile}
        narrative={narrative}
        narrativeLoading={narrativeMutation.isPending}
      />

      {/* Narrative error with retry */}
      {narrativeMutation.isError && (
        <div role="alert" className="flex items-center justify-center gap-3 text-sm">
          <p className="text-destructive">
            Could not generate your personalized summary.
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => narrativeMutation.mutate()}
          >
            Retry
          </Button>
        </div>
      )}

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
      <section className="space-y-4">
        {plan.job_matches.length > 0 ? (
          creditResult ? (
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
                  <h2 className="text-xl font-semibold text-accent-foreground">After Credit Repair</h2>
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
          )
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

      <Separator />

      {/* Comparison view */}
      <ComparisonView plan={plan} profile={profile} creditResult={creditResult} />

      {/* Export actions */}
      <Separator />
      <div className="flex flex-wrap items-center gap-3">
        <PlanExport plan={planWithNarrative} creditResult={creditResult} />
        <EmailExport plan={planWithNarrative} />
      </div>

      {/* Explore More Jobs — live listings from job_listings table */}
      {liveJobsLoading && (
        <>
          <Separator />
          <div className="flex items-center justify-center gap-2 py-8 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading live job listings...
          </div>
        </>
      )}
      {liveJobs && liveJobs.jobs.length > 0 && (
        <>
          <Separator />
          <section className="space-y-4">
            <h2 className="text-xl font-semibold text-primary">Explore More Jobs</h2>
            <p className="text-sm text-muted-foreground">
              Live job listings from Montgomery, AL job boards.
            </p>
            <div className="grid gap-4 sm:grid-cols-2">
              {liveJobs.jobs.map((job) => (
                <LiveJobCard key={`live-${job.id}`} job={job} />
              ))}
            </div>
          </section>
        </>
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
