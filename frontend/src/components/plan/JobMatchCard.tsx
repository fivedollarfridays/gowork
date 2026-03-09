"use client";

import { Briefcase, Bus, Car, CreditCard, DollarSign, ExternalLink, Footprints, MapPin, Shield } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import type { CreditAssessmentResult, JobMatch, ScoredJobMatch } from "@/lib/types";
import { STATUS_BADGE_STYLES, safeHref, daysToMonths, mapsUrl } from "@/lib/constants";
import { CliffBadge } from "./CliffBadge";
import { TransitInfoDisplay } from "./TransitInfoDisplay";

export function isScoredJob(job: JobMatch): job is ScoredJobMatch {
  return "relevance_score" in job;
}

function sourceLabel(source: string | null): string | null {
  if (!source) return null;
  if (source === "honestjobs") return "via Honest Jobs";
  if (source.startsWith("brightdata:")) return "via Indeed";
  if (source.startsWith("jsearch:")) return "via JSearch";
  return null;
}

interface JobMatchCardProps {
  job: JobMatch | ScoredJobMatch;
  creditResult?: CreditAssessmentResult | null;
}

export function JobMatchCard({ job, creditResult }: JobMatchCardProps) {
  const unmetThreshold = creditResult?.thresholds.find((t) => !t.already_met);
  const source = sourceLabel(job.source);
  const scored = isScoredJob(job);

  return (
    <Card>
      <CardHeader className="pb-2 space-y-2">
        {/* Title row */}
        <div className="flex flex-col items-center gap-1.5 text-center">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
            <Briefcase className="h-4 w-4 text-foreground/70" />
          </div>
          <CardTitle className="text-sm leading-tight">{job.title}</CardTitle>
          <p className="text-xs text-muted-foreground">
            {job.company}{source ? ` · ${source}` : ""}
          </p>
          {scored && job.relevance_score > 0 && (
            <Badge className="bg-secondary/10 text-secondary border-secondary/30 text-[10px]" variant="outline">
              {Math.round(job.relevance_score * 100)}% Match
            </Badge>
          )}
        </div>

        {/* Badges row */}
        <div className="flex flex-wrap justify-center gap-1">
          {job.transit_accessible ? (
            <Badge className={`${STATUS_BADGE_STYLES.positive} text-[10px] px-1.5 py-0`} variant="outline">
              <Bus className="h-2.5 w-2.5 mr-0.5" /> Bus
            </Badge>
          ) : (
            <Badge className={`${STATUS_BADGE_STYLES.warning} text-[10px] px-1.5 py-0`} variant="outline">
              <Bus className="h-2.5 w-2.5 mr-0.5" /> No Bus
            </Badge>
          )}
          {scored && job.pay_range ? (
            <Badge className={`${STATUS_BADGE_STYLES.positive} text-[10px] px-1.5 py-0`} variant="outline">
              <DollarSign className="h-2.5 w-2.5 mr-0.5" /> {job.pay_range}
            </Badge>
          ) : (
            <Badge className={`${STATUS_BADGE_STYLES.warning} text-[10px] px-1.5 py-0`} variant="outline">
              <DollarSign className="h-2.5 w-2.5 mr-0.5" /> No pay listed
            </Badge>
          )}
          {job.credit_check_required === "required" && (
            creditResult && job.eligible_now ? (
              <Badge className={`${STATUS_BADGE_STYLES.positive} text-[10px] px-1.5 py-0`} variant="outline">
                <CreditCard className="h-2.5 w-2.5 mr-0.5" /> Eligible
              </Badge>
            ) : creditResult ? (
              <Badge className={`${STATUS_BADGE_STYLES.warning} text-[10px] px-1.5 py-0`} variant="outline">
                <CreditCard className="h-2.5 w-2.5 mr-0.5" />
                {unmetThreshold ? daysToMonths(unmetThreshold.estimated_days) : "After Repair"}
              </Badge>
            ) : (
              <Badge className={`${STATUS_BADGE_STYLES.negative} text-[10px] px-1.5 py-0`} variant="outline">
                <CreditCard className="h-2.5 w-2.5 mr-0.5" /> Credit Check
              </Badge>
            )
          )}
          {job.fair_chance && (
            <Badge className={`${STATUS_BADGE_STYLES.positive} text-[10px] px-1.5 py-0`} variant="outline">
              <Shield className="h-2.5 w-2.5 mr-0.5" /> Fair Chance
            </Badge>
          )}
          {job.record_eligible === false && (
            <Badge className={`${STATUS_BADGE_STYLES.negative} text-[10px] px-1.5 py-0`} variant="outline">
              <Shield className="h-2.5 w-2.5 mr-0.5" /> Record Review
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-2 pt-0 text-center">
        {/* Benefits cliff impact badge */}
        {scored && <CliffBadge cliffImpact={job.cliff_impact ?? null} />}

        {/* Match reason for scored jobs */}
        {scored && job.match_reason && (
          <p className="text-xs text-secondary font-medium">{job.match_reason}</p>
        )}

        {/* Location + route */}
        <div className="flex flex-wrap items-center justify-center gap-2 text-xs">
          {job.location && (
            <a
              href={mapsUrl(job.location)}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-secondary hover:underline"
            >
              <MapPin className="h-3 w-3 shrink-0" aria-hidden="true" />
              {job.location}
            </a>
          )}
          {job.route && (
            <span className="flex items-center gap-1 text-muted-foreground">
              <Bus className="h-3 w-3 shrink-0" aria-hidden="true" />
              {job.route}
            </span>
          )}
        </div>

        {/* Commute estimate */}
        {scored && job.commute_estimate && (
          <div className="flex flex-wrap items-center justify-center gap-3 text-sm text-muted-foreground" aria-label="Estimated commute times">
            <span className="flex items-center gap-1.5" aria-label={`${job.commute_estimate.drive_min} minute drive`}>
              <Car className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
              {job.commute_estimate.drive_min} min drive
            </span>
            {job.commute_estimate.transit_min != null && (
              <span className="flex items-center gap-1.5" aria-label={`${job.commute_estimate.transit_min} minute transit`}>
                <Bus className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                {job.commute_estimate.transit_min} min transit
              </span>
            )}
            {job.commute_estimate.walk_min != null && (
              <span className="flex items-center gap-1.5" aria-label={`${job.commute_estimate.walk_min} minute walk`}>
                <Footprints className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                {job.commute_estimate.walk_min} min walk
              </span>
            )}
          </div>
        )}

        {/* Transit schedule info */}
        {scored && job.transit_info && (
          <>
            <Separator />
            <TransitInfoDisplay transitInfo={job.transit_info} />
          </>
        )}

        {/* Eligibility */}
        {!job.eligible_now && job.eligible_after && (
          <>
            <Separator />
            <p className="text-xs text-accent-foreground">
              Eligible after: {job.eligible_after}
            </p>
          </>
        )}

        {/* Record note */}
        {job.record_note && (
          <>
            <Separator />
            <p className="text-xs text-muted-foreground">
              {job.record_note}
            </p>
          </>
        )}

        {/* Apply link */}
        {(() => {
          const applyHref = job.url ? safeHref(job.url) : undefined;
          return applyHref ? (
            <Button variant="outline" size="sm" className="gap-1.5" asChild>
              <a href={applyHref} target="_blank" rel="noopener noreferrer">
                Apply <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </Button>
          ) : null;
        })()}
      </CardContent>
    </Card>
  );
}
