"use client";

import { Suspense, useMemo, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getPlan, generateNarrative } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { MondayMorning } from "@/components/plan/MondayMorning";
import { BarrierCardView } from "@/components/plan/BarrierCardView";
import { JobMatchCard } from "@/components/plan/JobMatchCard";
import { ComparisonView } from "@/components/plan/ComparisonView";
import { BarrierType, EmploymentStatus, AvailableHours } from "@/lib/types";
import type { PlanNarrative, UserProfile } from "@/lib/types";
import { barrierCountToSeverity } from "@/lib/constants";

function buildProfileFromPlan(sessionId: string, barriers: string[]): UserProfile {
  return {
    session_id: sessionId,
    zip_code: "",
    employment_status: EmploymentStatus.UNEMPLOYED,
    barrier_count: barriers.length,
    primary_barriers: barriers as UserProfile["primary_barriers"],
    barrier_severity: barrierCountToSeverity(barriers.length),
    needs_credit_assessment: barriers.includes(BarrierType.CREDIT),
    transit_dependent: barriers.includes(BarrierType.TRANSPORTATION),
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
    queryFn: () => getPlan(sessionId!),
    enabled: !!sessionId,
  });

  const narrativeMutation = useMutation({
    mutationFn: () => generateNarrative(sessionId!),
    onSuccess: (result) => {
      setNarrative(result);
      queryClient.invalidateQueries({ queryKey: ["plan", sessionId] });
    },
  });

  const plan = data?.plan ?? null;

  const profile = useMemo(
    () => data ? buildProfileFromPlan(data.session_id, data.barriers) : null,
    [data],
  );
  const planWithNarrative = useMemo(
    () => plan && narrative ? { ...plan, resident_summary: narrative.summary } : plan,
    [plan, narrative],
  );
  const handleGenerateNarrative = useCallback(
    async () => { await narrativeMutation.mutateAsync(); },
    [narrativeMutation],
  );

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
          {(error as Error).message.includes("404")
            ? "Session not found. It may have expired."
            : `Error: ${(error as Error).message}`}
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
        onGenerateNarrative={handleGenerateNarrative}
      />

      {/* AI narrative key actions */}
      {narrative && narrative.key_actions.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-xl font-semibold text-primary">Key Actions</h2>
          <ol className="list-decimal list-inside space-y-2 text-sm">
            {narrative.key_actions.map((action, i) => (
              <li key={i} className="text-foreground/90">{action}</li>
            ))}
          </ol>
        </section>
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

      <Separator />

      {/* Job matches */}
      {plan.job_matches.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-primary">Matched Jobs</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {plan.job_matches.map((job) => (
              <JobMatchCard key={`${job.title}-${job.company}`} job={job} />
            ))}
          </div>
        </section>
      )}

      <Separator />

      {/* Comparison view */}
      <ComparisonView plan={plan} profile={profile} />

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
