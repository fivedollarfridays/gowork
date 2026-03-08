"use client";

import { useMemo, type ReactNode } from "react";
import { ExternalLink, MapPin, Phone } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { ReEntryPlan, UserProfile } from "@/lib/types";
import { CAREER_CENTER, mapsUrl, safeHref } from "@/lib/constants";

interface ActionStep {
  title: string;
  location?: string;
  phone?: string;
  url?: string;
}

function getNextActionableDay(): string {
  const day = new Date().getDay();
  return day === 5 || day === 6 ? "Monday morning" : "tomorrow morning";
}

function buildSteps(plan: ReEntryPlan): ActionStep[] {
  const steps: ActionStep[] = [];

  for (const step of plan.immediate_next_steps) {
    if (step.includes(CAREER_CENTER.name)) {
      steps.push({
        title: CAREER_CENTER.name,
        phone: CAREER_CENTER.phone,
        location: CAREER_CENTER.address,
      });
    } else {
      steps.push({ title: step });
    }
  }

  const firstBarrier = plan.barriers[0];
  if (firstBarrier?.resources[0]) {
    const resource = firstBarrier.resources[0];
    steps.push({
      title: `Visit ${resource.name}`,
      location: resource.address ?? undefined,
      phone: resource.phone ?? undefined,
      url: resource.url ?? undefined,
    });
  }

  return steps.slice(0, 3);
}

interface MondayMorningProps {
  plan: ReEntryPlan;
  profile: UserProfile;
  firstStepAction?: ReactNode;
}

export function MondayMorning({ plan, profile, firstStepAction }: MondayMorningProps) {
  const steps = useMemo(() => buildSteps(plan), [plan]);

  return (
    <section className="space-y-8">
      <div className="space-y-3">
        <h1 className="text-3xl sm:text-4xl font-bold text-primary tracking-tight">
          Here&apos;s what you can do {getNextActionableDay()}.
        </h1>
        <p className="text-lg text-muted-foreground">
          Your personalized action plan for Montgomery, AL
          {profile.barrier_count > 0 && (
            <>, addressing {profile.barrier_count} barrier{profile.barrier_count > 1 ? "s" : ""}</>
          )}
        </p>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-primary mb-4">Your Next Steps</h2>
        <div className="flex flex-wrap justify-center gap-3">
          {steps.map((step, i) => (
            <Card key={i} className="group flex flex-col w-full sm:w-[calc(50%-0.375rem)] lg:w-[calc(33.333%-0.5rem)] transition-shadow duration-300 ease-in-out hover:shadow-md">
              <CardContent className="p-4 flex flex-col gap-2 flex-1">
                <div className="flex items-start gap-2">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-secondary text-secondary-foreground text-xs font-bold mt-0.5">
                    {i + 1}
                  </span>
                  <h3 className="text-sm font-semibold text-foreground leading-snug">{step.title}</h3>
                </div>

                {/* Details revealed on hover */}
                <div className="block sm:max-h-0 sm:overflow-hidden sm:group-hover:max-h-96 sm:group-focus-within:max-h-96 transition-[max-height,opacity] duration-300 ease-in-out sm:opacity-0 sm:group-hover:opacity-100 sm:group-focus-within:opacity-100 text-xs space-y-1.5 ml-8">
                  {step.phone && (
                    <a href={`tel:${step.phone}`} className="flex items-center gap-1 text-secondary hover:underline">
                      <Phone className="h-3 w-3" />
                      {step.phone}
                    </a>
                  )}
                  {step.location && (
                    <a
                      href={mapsUrl(step.location)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-secondary hover:underline"
                    >
                      <MapPin className="h-3 w-3" />
                      {step.location}
                    </a>
                  )}
                  {step.url && safeHref(step.url) && (
                    <a href={safeHref(step.url)} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-secondary hover:underline">
                      <ExternalLink className="h-3 w-3" />
                      Website
                    </a>
                  )}
                </div>

                {i === 0 && firstStepAction && (
                  <div className="mt-auto pt-2 flex justify-center">
                    {firstStepAction}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
