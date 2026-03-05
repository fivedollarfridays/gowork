"use client";

import { useSearchParams } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";
import { getPlan, generateNarrative } from "@/lib/api";
import type { PlanNarrative } from "@/lib/types";
import { Suspense, useState } from "react";

function PlanContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session");
  const [narrative, setNarrative] = useState<PlanNarrative | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["plan", sessionId],
    queryFn: () => getPlan(sessionId!),
    enabled: !!sessionId,
  });

  const narrativeMutation = useMutation({
    mutationFn: () => generateNarrative(sessionId!),
    onSuccess: (data) => setNarrative(data),
  });

  if (!sessionId) {
    return (
      <div className="text-center">
        <p className="text-muted-foreground">No session ID provided.</p>
        <a href="/assess" className="text-primary underline mt-2 inline-block">Start an assessment</a>
      </div>
    );
  }

  if (isLoading) return <p className="text-muted-foreground">Loading plan...</p>;
  if (error) return <p className="text-red-500">Error: {(error as Error).message}</p>;
  if (!data) return null;

  const plan = data.plan;

  return (
    <div className="space-y-6">
      <div className="rounded-lg border p-4 bg-blue-50">
        <h2 className="font-semibold">Session: {data.session_id}</h2>
        <p className="text-sm text-muted-foreground">
          Barriers: {data.barriers.join(", ") || "None"}
        </p>
      </div>

      {!plan && (
        <div className="rounded-lg border p-4 bg-yellow-50">
          <p>No plan generated yet. Complete an assessment first.</p>
          <a href="/assess" className="text-primary underline">Go to assessment</a>
        </div>
      )}

      {plan && (
        <>
          {(narrative || plan.resident_summary) && (
            <div className="rounded-lg border p-4 bg-green-50">
              <h3 className="font-medium mb-2">Your Monday Morning Plan</h3>
              <p>{narrative?.summary || plan.resident_summary}</p>
              {(narrative?.key_actions || []).length > 0 && (
                <ol className="list-decimal list-inside mt-3 space-y-1">
                  {narrative!.key_actions.map((action, i) => (
                    <li key={i}>{action}</li>
                  ))}
                </ol>
              )}
            </div>
          )}

          {!narrative && !plan.resident_summary && (
            <div className="rounded-lg border p-4">
              <p className="text-sm text-muted-foreground mb-2">
                Generate a personalized narrative summary of your plan.
              </p>
              <button
                onClick={() => narrativeMutation.mutate()}
                disabled={narrativeMutation.isPending}
                className="rounded-lg bg-primary px-6 py-2 text-primary-foreground font-medium disabled:opacity-50"
              >
                {narrativeMutation.isPending ? "Generating..." : "Generate AI Summary"}
              </button>
              {narrativeMutation.isError && (
                <p className="text-sm text-red-500 mt-2">{narrativeMutation.error.message}</p>
              )}
            </div>
          )}

          {plan.immediate_next_steps.length > 0 && (
            <div className="rounded-lg border p-4">
              <h3 className="font-medium mb-2">Immediate Next Steps</h3>
              <ol className="list-decimal list-inside space-y-1">
                {plan.immediate_next_steps.map((s, i) => <li key={i}>{s}</li>)}
              </ol>
            </div>
          )}

          {plan.barriers.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-medium">Barrier Timeline</h3>
              {plan.barriers.map((card, i) => (
                <div key={i} className="rounded-lg border p-4">
                  <div className="flex justify-between">
                    <span className="font-medium">{card.title}</span>
                    {card.timeline_days && (
                      <span className="text-sm text-muted-foreground">~{card.timeline_days} days</span>
                    )}
                  </div>
                  <ul className="list-disc list-inside mt-2 text-sm">
                    {card.actions.map((a, j) => <li key={j}>{a}</li>)}
                  </ul>
                  {card.resources.length > 0 && (
                    <div className="mt-2 text-sm text-muted-foreground">
                      <strong>Resources:</strong>{" "}
                      {card.resources.map((r) => r.name).join(", ")}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {plan.job_matches.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-medium">Matched Jobs</h3>
              {plan.job_matches.map((job, i) => (
                <div key={i} className="rounded-lg border p-4 flex justify-between items-center">
                  <div>
                    <span className="font-medium">{job.title}</span>
                    {job.company && <span className="text-muted-foreground"> — {job.company}</span>}
                    {!job.eligible_now && job.eligible_after && (
                      <p className="text-xs text-amber-600">Available after: {job.eligible_after}</p>
                    )}
                  </div>
                  {job.url && (
                    <a href={job.url} target="_blank" rel="noopener noreferrer" className="text-primary text-sm underline">
                      Apply
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function PlanPage() {
  return (
    <main className="min-h-screen p-8 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-primary mb-8">Career Plan</h1>
      <Suspense fallback={<p className="text-muted-foreground">Loading...</p>}>
        <PlanContent />
      </Suspense>
    </main>
  );
}
