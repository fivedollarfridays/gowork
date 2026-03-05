"use client";

import { useMemo } from "react";
import { ExternalLink, MapPin, Phone, Sparkles, Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { PlanNarrative, ReEntryPlan, UserProfile } from "@/lib/types";
import { safeHref } from "@/lib/constants";

interface ActionStep {
  title: string;
  detail: string;
  location?: string;
  phone?: string;
  url?: string;
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
      phone: resource.phone ?? undefined,
      url: resource.url ?? undefined,
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
          ? "Apply online"
          : "Contact employer directly",
      location: firstJob.location ?? undefined,
      url: firstJob.url ?? undefined,
    });
  }

  return steps.slice(0, 5);
}

interface MondayMorningProps {
  plan: ReEntryPlan;
  profile: UserProfile;
  narrative: PlanNarrative | null;
  narrativeLoading: boolean;
}

export function MondayMorning({ plan, profile, narrative, narrativeLoading }: MondayMorningProps) {
  const steps = useMemo(() => buildSteps(plan), [plan]);
  const allResources = useMemo(
    () => plan.barriers.flatMap((b) => b.resources),
    [plan],
  );

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
      {narrativeLoading && (
        <div aria-live="polite">
        <Card className="bg-secondary/5 border-secondary/20">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin text-secondary" />
              <p className="text-sm">Generating your personalized summary...</p>
            </div>
          </CardContent>
        </Card>
        </div>
      )}
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

      {/* Key actions from AI — inline with links */}
      {narrative && narrative.key_actions.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-primary">Key Actions</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {narrative.key_actions.map((action, i) => {
              const matchedResource = allResources
                .find((r) => action.toLowerCase().includes(r.name.toLowerCase()));

              return (
                <Card key={i}>
                  <CardContent className="p-4 space-y-2">
                    <p className="text-sm font-medium text-foreground">{action}</p>
                    {matchedResource && (
                      <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                        {matchedResource.phone && (
                          <a href={`tel:${matchedResource.phone}`} className="flex items-center gap-1 text-secondary hover:underline">
                            <Phone className="h-3 w-3" />
                            {matchedResource.phone}
                          </a>
                        )}
                        {matchedResource.address && (
                          <a
                            href={`https://maps.google.com/?q=${encodeURIComponent(matchedResource.address)}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-secondary hover:underline"
                          >
                            <MapPin className="h-3 w-3" />
                            Directions
                          </a>
                        )}
                        {matchedResource.url && safeHref(matchedResource.url) && (
                          <a href={safeHref(matchedResource.url)} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-secondary hover:underline">
                            <ExternalLink className="h-3 w-3" />
                            Website
                          </a>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
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
                  <div className="flex flex-wrap gap-3 mt-2">
                    {step.phone && (
                      <a href={`tel:${step.phone}`} className="flex items-center gap-1 text-xs text-secondary hover:underline">
                        <Phone className="h-3 w-3" />
                        {step.phone}
                      </a>
                    )}
                    {step.location && (
                      <a
                        href={`https://maps.google.com/?q=${encodeURIComponent(step.location)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs text-secondary hover:underline"
                      >
                        <MapPin className="h-3 w-3" />
                        {step.location}
                      </a>
                    )}
                    {step.url && safeHref(step.url) && (
                      <a href={safeHref(step.url)} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-xs text-secondary hover:underline">
                        <ExternalLink className="h-3 w-3" />
                        Visit Website
                      </a>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
