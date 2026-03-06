"use client";

import { useMemo, type ReactNode } from "react";
import { ExternalLink, MapPin, Phone } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { ReEntryPlan, UserProfile } from "@/lib/types";
import { safeHref } from "@/lib/constants";

interface ActionStep {
  title: string;
  detail: string;
  location?: string;
  phone?: string;
  url?: string;
}

function getNextActionableDay(): string {
  const day = new Date().getDay();
  // Friday (5) or Saturday (6) → "Monday morning"
  // All other days → "tomorrow morning"
  return day === 5 || day === 6 ? "Monday morning" : "tomorrow morning";
}

function mapsUrl(address: string): string {
  return `https://maps.google.com/?q=${encodeURIComponent(address)}`;
}

const PHONE_RE = /(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})/;

function linkifyPhones(text: string): ReactNode {
  const parts = text.split(PHONE_RE);
  if (parts.length === 1) return text;
  return parts.map((part, i) =>
    PHONE_RE.test(part) ? (
      <a key={i} href={`tel:${part}`} className="text-secondary hover:underline">
        {part}
      </a>
    ) : (
      part
    ),
  );
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
      detail: resource.phone ? "Call ahead" : "Bring your ID and any relevant documents",
      location: resource.address ?? undefined,
      phone: resource.phone ?? undefined,
      url: resource.url ?? undefined,
    });
  }

  // Add top strong match, or fallback to first eligible job
  const firstJob = plan.strong_matches?.[0] ?? plan.job_matches.find((j) => j.eligible_now);
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
}

export function MondayMorning({ plan, profile }: MondayMorningProps) {
  const steps = useMemo(() => buildSteps(plan), [plan]);

  return (
    <section className="space-y-8">
      {/* Hero header */}
      <div className="space-y-3">
        <h1 className="text-3xl sm:text-4xl font-bold text-primary tracking-tight">
          Here&apos;s what you can do {getNextActionableDay()}.
        </h1>
        <p className="text-lg text-muted-foreground">
          Your personalized action plan for Montgomery, AL
          {profile.barrier_count > 0 && (
            <> — addressing {profile.barrier_count} barrier{profile.barrier_count > 1 ? "s" : ""}</>
          )}
        </p>
      </div>

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
                  <h3 className="font-semibold text-foreground">{linkifyPhones(step.title)}</h3>
                  <p className="text-sm text-muted-foreground mt-1">{linkifyPhones(step.detail)}</p>
                  <div className="flex flex-wrap gap-3 mt-2">
                    {step.phone && (
                      <a href={`tel:${step.phone}`} className="flex items-center gap-1 text-xs text-secondary hover:underline">
                        <Phone className="h-3 w-3" />
                        {step.phone}
                      </a>
                    )}
                    {step.location && (
                      <a
                        href={mapsUrl(step.location)}
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
