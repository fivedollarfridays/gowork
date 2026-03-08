"use client";

import { useMemo, type ReactNode } from "react";
import { Briefcase, ExternalLink, MapPin, Phone, Shield, Clock } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import type { BarrierCard, ReEntryPlan, ScoredJobMatch, UserProfile } from "@/lib/types";
import { CAREER_CENTER, mapsUrl, safeHref, humanizeLabel, toTelHref } from "@/lib/constants";

function getNextActionableDay(): string {
  const day = new Date().getDay();
  return day === 5 || day === 6 ? "Monday morning" : "tomorrow morning";
}

function getTopJobs(plan: ReEntryPlan): ScoredJobMatch[] {
  const all = [...plan.job_matches];
  // Prefer jobs with disclosed pay, then by relevance score
  all.sort((a, b) => {
    const aPay = a.pay_range ? 1 : 0;
    const bPay = b.pay_range ? 1 : 0;
    if (aPay !== bPay) return bPay - aPay;
    return b.relevance_score - a.relevance_score;
  });
  const seen = new Set<string>();
  const unique: ScoredJobMatch[] = [];
  for (const job of all) {
    const key = `${job.title}|${job.company}`;
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(job);
    }
    if (unique.length >= 3) break;
  }
  return unique;
}

const stepNumber = "flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold";

interface MondayMorningProps {
  plan: ReEntryPlan;
  profile: UserProfile;
  firstStepAction?: ReactNode;
}

export function MondayMorning({ plan, profile, firstStepAction }: MondayMorningProps) {
  const topJobs = useMemo(() => getTopJobs(plan), [plan]);

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
        <div className="grid gap-4 sm:grid-cols-3">
          <CareerCenterStep action={firstStepAction} />
          <JobsStep jobs={topJobs} />
          <BarrierStep barriers={plan.barriers} />
        </div>
      </div>
    </section>
  );
}

function CareerCenterStep({ action }: { action?: ReactNode }) {
  return (
    <Card className="flex flex-col transition-shadow hover:shadow-md">
      <CardContent className="p-4 flex flex-col gap-3 flex-1">
        <div className="flex items-start gap-2">
          <span className={stepNumber}>1</span>
          <h3 className="text-sm font-semibold text-foreground leading-snug pt-0.5">
            Visit the Career Center
          </h3>
        </div>

        <p className="text-xs text-muted-foreground ml-9">
          Bring your Career Center Ready Package. A case manager will review your plan and connect you with services.
        </p>

        <div className="text-xs space-y-1.5 ml-9">
          <a
            href={mapsUrl(CAREER_CENTER.address)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-secondary hover:underline"
          >
            <MapPin className="h-3.5 w-3.5 shrink-0" />
            {CAREER_CENTER.address}
          </a>
          <a
            href={toTelHref(CAREER_CENTER.phone)}
            className="flex items-center gap-1.5 text-secondary hover:underline"
          >
            <Phone className="h-3.5 w-3.5 shrink-0" />
            {CAREER_CENTER.phone}
          </a>
          <p className="flex items-center gap-1.5 text-muted-foreground">
            <Clock className="h-3.5 w-3.5 shrink-0" />
            {CAREER_CENTER.hours}
          </p>
        </div>

        {action && (
          <div className="mt-auto pt-2 flex justify-center">
            {action}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function JobsStep({ jobs }: { jobs: ScoredJobMatch[] }) {
  const scrollToJobs = () => {
    document.getElementById("matched-jobs")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <Card className="flex flex-col transition-shadow hover:shadow-md">
      <CardContent className="p-4 flex flex-col gap-3 flex-1">
        <div className="flex items-start gap-2">
          <span className={stepNumber}>2</span>
          <h3 className="text-sm font-semibold text-foreground leading-snug pt-0.5">
            Review Your Job Matches
          </h3>
        </div>

        {jobs.length > 0 ? (
          <ul className="text-xs space-y-2 ml-9">
            {jobs.map((job, i) => (
              <li key={`${job.title}-${job.company}-${i}`}>
                <button
                  type="button"
                  onClick={scrollToJobs}
                  className="flex items-start gap-1.5 text-left text-secondary hover:underline"
                >
                  <Briefcase className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                  <span>
                    <span className="font-medium">{job.title}</span>
                    {job.company && <span className="text-muted-foreground"> at {job.company}</span>}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted-foreground ml-9">
            No matches yet — check back after updating your assessment.
          </p>
        )}

        {jobs.length > 0 && (
          <button
            type="button"
            onClick={scrollToJobs}
            className="mt-auto text-xs text-secondary hover:underline ml-9"
          >
            View all matches &darr;
          </button>
        )}
      </CardContent>
    </Card>
  );
}

function BarrierStep({ barriers }: { barriers: BarrierCard[] }) {
  if (barriers.length === 0) {
    return (
      <Card className="flex flex-col transition-shadow hover:shadow-md">
        <CardContent className="p-4 flex flex-col gap-3 flex-1">
          <div className="flex items-start gap-2">
            <span className={stepNumber}>3</span>
            <h3 className="text-sm font-semibold text-foreground leading-snug pt-0.5">
              No Barriers Identified
            </h3>
          </div>
          <p className="text-xs text-muted-foreground ml-9">
            Great news — no barriers were found. Focus on your job search!
          </p>
        </CardContent>
      </Card>
    );
  }

  const primary = barriers[0];
  const additional = barriers.slice(1);

  return (
    <Card className="flex flex-col transition-shadow hover:shadow-md">
      <CardContent className="p-4 flex flex-col gap-3 flex-1">
        <div className="flex items-start gap-2">
          <span className={stepNumber}>3</span>
          <h3 className="text-sm font-semibold text-foreground leading-snug pt-0.5">
            Address Your Barriers
          </h3>
        </div>

        <BarrierDetail barrier={primary} />

        {additional.length > 0 && (
          <Accordion type="single" collapsible className="ml-9">
            <AccordionItem value="more" className="border-b-0">
              <AccordionTrigger className="py-2 text-xs text-muted-foreground hover:no-underline">
                {additional.length} more barrier{additional.length > 1 ? "s" : ""}
              </AccordionTrigger>
              <AccordionContent className="space-y-4">
                {additional.map((b) => (
                  <BarrierDetail key={b.type} barrier={b} />
                ))}
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        )}
      </CardContent>
    </Card>
  );
}

function BarrierDetail({ barrier }: { barrier: BarrierCard }) {
  const resource = barrier.resources[0];

  return (
    <div className="ml-9 space-y-2">
      <div className="flex items-center gap-1.5">
        <Shield className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
        <span className="text-xs font-medium">{humanizeLabel(barrier.type)}</span>
      </div>

      {barrier.actions[0] && (
        <p className="text-xs text-muted-foreground">{barrier.actions[0]}</p>
      )}

      {resource && (
        <div className="text-xs space-y-1">
          <p className="font-medium text-foreground">{resource.name}</p>
          {resource.phone && (
            <a
              href={toTelHref(resource.phone)}
              className="flex items-center gap-1.5 text-secondary hover:underline"
            >
              <Phone className="h-3 w-3 shrink-0" />
              {resource.phone}
            </a>
          )}
          {resource.address && (
            <a
              href={mapsUrl(resource.address)}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-secondary hover:underline"
            >
              <MapPin className="h-3 w-3 shrink-0" />
              {resource.address}
            </a>
          )}
          {resource.url && safeHref(resource.url) && (
            <a
              href={safeHref(resource.url)}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-secondary hover:underline"
            >
              <ExternalLink className="h-3 w-3 shrink-0" />
              Website
            </a>
          )}
        </div>
      )}
    </div>
  );
}
