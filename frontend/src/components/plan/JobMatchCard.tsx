"use client";

import { Briefcase, Bus, CreditCard, DollarSign, ExternalLink, MapPin, Shield } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import type { CreditAssessmentResult, JobMatch, ScoredJobMatch } from "@/lib/types";
import { STATUS_BADGE_STYLES, safeHref, daysToMonths, mapsUrl } from "@/lib/constants";
import { CliffBadge } from "./CliffBadge";

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

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
              <Briefcase className="h-5 w-5 text-foreground/70" />
            </div>
            <div>
              <CardTitle className="text-base">{job.title}</CardTitle>
              {job.company && (
                <p className="text-sm text-muted-foreground">{job.company}</p>
              )}
              {source && (
                <p className="text-xs text-muted-foreground/70">{source}</p>
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {/* Relevance score badge */}
            {isScoredJob(job) && job.relevance_score > 0 && (
              <Badge className="bg-secondary/10 text-secondary border-secondary/30 text-xs" variant="outline">
                {Math.round(job.relevance_score * 100)}% Match
              </Badge>
            )}
            {/* Transit badge */}
            {job.transit_accessible ? (
              <Badge className={`${STATUS_BADGE_STYLES.positive} text-xs`} variant="outline">
                <Bus className="h-3 w-3 mr-1" />
                Bus Accessible
              </Badge>
            ) : (
              <Badge className={`${STATUS_BADGE_STYLES.warning} text-xs`} variant="outline">
                <Bus className="h-3 w-3 mr-1" />
                Requires Transport
              </Badge>
            )}
            {/* Pay badge */}
            {isScoredJob(job) && job.pay_range ? (
              <Badge className={`${STATUS_BADGE_STYLES.positive} text-xs`} variant="outline">
                <DollarSign className="h-3 w-3 mr-1" />
                {job.pay_range}
              </Badge>
            ) : (
              <Badge className={`${STATUS_BADGE_STYLES.warning} text-xs`} variant="outline">
                <DollarSign className="h-3 w-3 mr-1" />
                Pay not disclosed
              </Badge>
            )}
            {job.credit_check_required === "required" && (
              creditResult && job.eligible_now ? (
                <Badge className={`${STATUS_BADGE_STYLES.positive} text-xs`} variant="outline">
                  <CreditCard className="h-3 w-3 mr-1" />
                  Eligible Now
                </Badge>
              ) : creditResult ? (
                <Badge className={`${STATUS_BADGE_STYLES.warning} text-xs`} variant="outline">
                  <CreditCard className="h-3 w-3 mr-1" />
                  {unmetThreshold
                    ? daysToMonths(unmetThreshold.estimated_days)
                    : "After Repair"}
                </Badge>
              ) : (
                <Badge className={`${STATUS_BADGE_STYLES.negative} text-xs`} variant="outline">
                  <CreditCard className="h-3 w-3 mr-1" />
                  Credit Check
                </Badge>
              )
            )}
            {/* Fair-chance badge */}
            {job.fair_chance && (
              <Badge className={`${STATUS_BADGE_STYLES.positive} text-xs`} variant="outline">
                <Shield className="h-3 w-3 mr-1" />
                Fair Chance
              </Badge>
            )}
            {/* Record not eligible badge */}
            {job.record_eligible === false && (
              <Badge className={`${STATUS_BADGE_STYLES.negative} text-xs`} variant="outline">
                <Shield className="h-3 w-3 mr-1" />
                Record Review Needed
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Benefits cliff impact badge */}
        {isScoredJob(job) && <CliffBadge cliffImpact={job.cliff_impact ?? null} />}

        {/* Match reason for scored jobs */}
        {isScoredJob(job) && job.match_reason && (
          <p className="text-sm text-secondary font-medium">{job.match_reason}</p>
        )}

        {/* Location + route */}
        <div className="flex flex-wrap items-center gap-3 text-sm">
          {job.location && (
            <a
              href={mapsUrl(job.location)}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-secondary hover:underline"
            >
              <MapPin className="h-3.5 w-3.5 shrink-0" />
              {job.location}
            </a>
          )}
          {job.route && (
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <Bus className="h-3.5 w-3.5 shrink-0" />
              {job.route}
            </span>
          )}
        </div>

        {/* Eligibility */}
        {!job.eligible_now && job.eligible_after && (
          <>
            <Separator />
            <p className="text-sm text-accent-foreground">
              Eligible after: {job.eligible_after}
            </p>
          </>
        )}

        {/* Record note */}
        {job.record_note && (
          <>
            <Separator />
            <p className="text-sm text-muted-foreground">
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
