"use client";

import { useMemo, useState } from "react";
import { MapPin, Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { ReEntryPlan, UserProfile } from "@/lib/types";

interface ActionStep {
  title: string;
  detail: string;
  location?: string;
}

function buildSteps(plan: ReEntryPlan): ActionStep[] {
  const steps: ActionStep[] = [];

  // Start with immediate_next_steps
  for (const step of plan.immediate_next_steps) {
    steps.push({ title: step, detail: "Priority action from your personalized plan" });
  }

  // Add first resource from first barrier card
  const firstBarrier = plan.barriers[0];
  if (firstBarrier?.resources[0]) {
    const resource = firstBarrier.resources[0];
    steps.push({
      title: `Visit ${resource.name}`,
      detail: resource.phone ? `Call ahead: ${resource.phone}` : "Bring your ID and any relevant documents",
      location: resource.address ?? undefined,
    });
  }

  // Add first eligible job match
  const firstJob = plan.job_matches.find((j) => j.eligible_now);
  if (firstJob) {
    steps.push({
      title: `Apply for ${firstJob.title}${firstJob.company ? ` at ${firstJob.company}` : ""}`,
      detail: firstJob.route
        ? `Transit accessible via ${firstJob.route}`
        : firstJob.url
          ? "Apply online — link in your plan"
          : "Contact employer directly",
      location: firstJob.location ?? undefined,
    });
  }

  return steps.slice(0, 5);
}

interface MondayMorningProps {
  plan: ReEntryPlan;
  profile: UserProfile;
  onGenerateNarrative: () => Promise<void>;
}

export function MondayMorning({ plan, profile, onGenerateNarrative }: MondayMorningProps) {
  const [generating, setGenerating] = useState(false);
  const steps = useMemo(() => buildSteps(plan), [plan]);

  async function handleGenerate() {
    setGenerating(true);
    try {
      await onGenerateNarrative();
    } finally {
      setGenerating(false);
    }
  }

  return (
    <section className="space-y-8">
      {/* Hero header */}
      <div className="space-y-3">
        <h1 className="text-3xl sm:text-4xl font-bold text-primary tracking-tight">
          Here&apos;s what you can do Monday morning.
        </h1>
        <p className="text-lg text-muted-foreground">
          Your personalized action plan for Montgomery, AL
          {profile.barrier_count > 0 && (
            <> — addressing {profile.barrier_count} barrier{profile.barrier_count > 1 ? "s" : ""}</>
          )}
        </p>
      </div>

      {/* AI narrative */}
      {plan.resident_summary && (
        <>
          <Card className="bg-secondary/5 border-secondary/20">
            <CardContent className="p-6">
              <div className="flex items-start gap-3">
                <Sparkles className="h-5 w-5 text-secondary shrink-0 mt-0.5" />
                <p className="text-base leading-relaxed italic text-foreground/90">
                  {plan.resident_summary}
                </p>
              </div>
            </CardContent>
          </Card>
          <Separator />
        </>
      )}

      {/* Action steps timeline */}
      <div className="space-y-1">
        <h2 className="text-xl font-semibold text-primary mb-6">Your Next Steps</h2>
        <div className="relative">
          {steps.map((step, i) => (
            <div key={i} className="flex gap-4 pb-8 last:pb-0">
              {/* Timeline connector */}
              <div className="flex flex-col items-center">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary text-secondary-foreground text-sm font-bold">
                  {i + 1}
                </div>
                {i < steps.length - 1 && (
                  <div className="w-0.5 flex-1 bg-secondary/30 mt-1" />
                )}
              </div>

              {/* Step content */}
              <Card className="flex-1">
                <CardContent className="p-4">
                  <h3 className="font-semibold text-foreground">{step.title}</h3>
                  <p className="text-sm text-muted-foreground mt-1">{step.detail}</p>
                  {step.location && (
                    <div className="flex items-center gap-1.5 mt-2 text-xs text-muted-foreground">
                      <MapPin className="h-3 w-3" />
                      <span>{step.location}</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
      </div>

      {/* Generate AI Summary CTA */}
      {!plan.resident_summary && (
        <div className="flex flex-col items-center gap-3 py-4">
          <Separator className="mb-2" />
          <p className="text-sm text-muted-foreground text-center">
            Want a personalized narrative summary of your plan?
          </p>
          <Button
            onClick={handleGenerate}
            disabled={generating}
            size="lg"
            className="gap-2"
          >
            {generating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Generate AI Summary
              </>
            )}
          </Button>
        </div>
      )}
    </section>
  );
}
