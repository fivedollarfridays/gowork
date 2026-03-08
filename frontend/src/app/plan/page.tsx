"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getPlan, getJobs } from "@/lib/api";
import { Briefcase, Clock, ExternalLink, Loader2, MapPin, Phone, Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { MondayMorning } from "@/components/plan/MondayMorning";
import { BarrierCardView } from "@/components/plan/BarrierCardView";
import { JobMatchCard } from "@/components/plan/JobMatchCard";
import { JobBucketSection } from "@/components/plan/JobBucketSection";
import { ComparisonView } from "@/components/plan/ComparisonView";
import { CreditResults } from "@/components/plan/CreditResults";
import { JobReadinessResults } from "@/components/plan/JobReadinessResults";
import { CareerCenterExport } from "@/components/plan/CareerCenterExport";
import { EmailExport } from "@/components/plan/EmailExport";
import { PlanExport } from "@/components/plan/PlanExport";
import { EmptyState } from "@/components/EmptyState";
import { BarrierType, EmploymentStatus, AvailableHours } from "@/lib/types";
import type { CreditAssessmentResult, EnrichedJob, UserProfile } from "@/lib/types";
import { barrierCountToSeverity, CAREER_CENTER, safeHref } from "@/lib/constants";

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
          {job.credit_check_required === "required" && (
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

function useSessionId(): string | null {
  const searchParams = useSearchParams();
  const fromUrl = searchParams.get("session");

  useEffect(() => {
    if (fromUrl) {
      try { sessionStorage.setItem("montgowork_session_id", fromUrl); } catch {}
    }
  }, [fromUrl]);

  if (fromUrl) {
    return fromUrl;
  }

  try { return sessionStorage.getItem("montgowork_session_id"); } catch {}
  return null;
}

function useToken(sessionId: string | null): string | null {
  const searchParams = useSearchParams();
  const fromUrl = searchParams.get("token");

  useEffect(() => {
    if (fromUrl && sessionId) {
      try { sessionStorage.setItem(`feedback_token_${sessionId}`, fromUrl); } catch {}
    }
  }, [fromUrl, sessionId]);

  if (fromUrl) return fromUrl;
  if (!sessionId || typeof window === "undefined") return null;
  try { return sessionStorage.getItem(`feedback_token_${sessionId}`); } catch {}
  return null;
}

function PlanContent() {
  const sessionId = useSessionId();
  const token = useToken(sessionId);

  const { data, isLoading, error } = useQuery({
    queryKey: ["plan", sessionId, token],
    queryFn: () => getPlan(sessionId ?? "", token ?? undefined),
    enabled: !!sessionId && !!token,
  });

  const barriers = data?.barriers ?? [];
  const barrierParam = barriers.length > 0 ? barriers.join(",") : undefined;

  const { data: liveJobs, isLoading: liveJobsLoading } = useQuery({
    queryKey: ["liveJobs", barrierParam],
    queryFn: () => getJobs({ barriers: barrierParam }),
    enabled: !!data,
  });

  const plan = data?.plan ?? null;

  // Load credit assessment: sessionStorage first (faster), backend fallback
  const [localCredit] = useState<CreditAssessmentResult | null>(() => {
    if (!sessionId || typeof window === "undefined") return null;
    try {
      const stored = sessionStorage.getItem(`credit_${sessionId}`);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const creditResult = localCredit ?? data?.credit_profile ?? null;

  const profile = useMemo(
    () => data ? buildProfileFromPlan(data.session_id, data.barriers) : null,
    [data],
  );

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
      <MondayMorning
        plan={plan}
        profile={profile}
      />

      <Separator />

      {/* Barrier cards */}
      {plan.barriers.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-primary">Your Barriers</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {plan.barriers.map((barrier) => (
              <BarrierCardView key={barrier.type} barrier={barrier} sessionId={sessionId ?? undefined} token={token ?? undefined} />
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

      {/* Job Readiness Score */}
      {plan.job_readiness && (
        <>
          <Separator />
          <section className="space-y-4">
            <h2 className="text-xl font-semibold text-primary">Job Readiness</h2>
            <JobReadinessResults result={plan.job_readiness} />
          </section>
        </>
      )}

      <Separator />

      {/* Job matches — three-bucket display */}
      <section className="space-y-6">
        {(plan.strong_matches?.length ?? 0) > 0 || (plan.possible_matches?.length ?? 0) > 0 || (plan.after_repair?.length ?? 0) > 0 ? (
          <>
            <JobBucketSection
              title="Jobs That Match Your Profile"
              jobs={plan.strong_matches ?? []}
            />
            <JobBucketSection
              title="Worth Exploring"
              jobs={plan.possible_matches ?? []}
            />
            <JobBucketSection
              title="After Credit Repair"
              jobs={plan.after_repair ?? []}
              description="These jobs require a credit check. Follow your credit repair plan to become eligible."
            />
          </>
        ) : (plan.job_matches?.length ?? 0) > 0 ? (
          <>
            <h2 className="text-xl font-semibold text-primary">Matched Jobs</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              {plan.job_matches.map((job, i) => (
                <JobMatchCard key={`job-${job.title}-${job.company}-${i}`} job={job} creditResult={creditResult} />
              ))}
            </div>
          </>
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
        <CareerCenterExport sessionId={sessionId} token={token ?? undefined} />
        <PlanExport plan={plan} creditResult={creditResult} feedbackToken={token} />
        <EmailExport sessionId={sessionId} token={token ?? undefined} />
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

      {/* What's Next CTA */}
      <Separator />
      <Card className="border-secondary/30 bg-secondary/5">
        <CardHeader>
          <CardTitle className="text-xl">What&apos;s Next?</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <ol className="list-decimal list-inside space-y-3 text-sm">
            <li><strong>Print or download your plan</strong> using the export buttons above.</li>
            <li><strong>Bring this plan to the Montgomery Career Center:</strong></li>
          </ol>
          <div className="ml-6 space-y-1.5 text-sm text-muted-foreground">
            <p className="flex items-center gap-2"><MapPin className="h-4 w-4 shrink-0" /> {CAREER_CENTER.address}</p>
            <p className="flex items-center gap-2"><Phone className="h-4 w-4 shrink-0" /> {CAREER_CENTER.phone}</p>
            <p className="flex items-center gap-2"><Clock className="h-4 w-4 shrink-0" /> {CAREER_CENTER.hours}</p>
          </div>
          <ol start={3} className="list-decimal list-inside space-y-3 text-sm">
            <li><strong>Ask for a case manager</strong> and show them your Career Center Ready Package.</li>
          </ol>
          <div className="pt-2">
            <Button asChild variant="outline" size="sm">
              <a href="/assess">Start New Assessment</a>
            </Button>
          </div>
        </CardContent>
      </Card>

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
