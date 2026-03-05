"use client";

import { Briefcase, Bus, CreditCard, ExternalLink, MapPin } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import type { CreditAssessmentResult, JobMatch } from "@/lib/types";
import { STATUS_BADGE_STYLES, safeHref } from "@/lib/constants";

interface JobMatchCardProps {
  job: JobMatch;
  creditResult?: CreditAssessmentResult | null;
}

export function JobMatchCard({ job, creditResult }: JobMatchCardProps) {
  const unmetThreshold = creditResult?.thresholds.find((t) => !t.already_met);

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
            </div>
          </div>
          <div className="flex flex-wrap gap-1.5">
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
            {job.credit_check_required === "yes" && (
              creditResult && job.eligible_now ? (
                <Badge className={`${STATUS_BADGE_STYLES.positive} text-xs`} variant="outline">
                  <CreditCard className="h-3 w-3 mr-1" />
                  Eligible Now
                </Badge>
              ) : creditResult ? (
                <Badge className={`${STATUS_BADGE_STYLES.warning} text-xs`} variant="outline">
                  <CreditCard className="h-3 w-3 mr-1" />
                  {unmetThreshold
                    ? `~${Math.round(unmetThreshold.estimated_days / 30)}mo`
                    : "After Repair"}
                </Badge>
              ) : (
                <Badge className={`${STATUS_BADGE_STYLES.negative} text-xs`} variant="outline">
                  <CreditCard className="h-3 w-3 mr-1" />
                  Credit Check
                </Badge>
              )
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Location + route */}
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          {job.location && (
            <span className="flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" />
              {job.location}
            </span>
          )}
          {job.route && (
            <span className="flex items-center gap-1">
              <Bus className="h-3.5 w-3.5" />
              {job.route}
            </span>
          )}
        </div>

        {/* Eligibility */}
        {!job.eligible_now && job.eligible_after && (
          <>
            <Separator />
            <p className="text-sm text-amber-600">
              Eligible after: {job.eligible_after}
            </p>
          </>
        )}

        {/* Apply link */}
        {job.url && safeHref(job.url) && (
          <Button variant="outline" size="sm" className="gap-1.5" asChild>
            <a href={safeHref(job.url)} target="_blank" rel="noopener noreferrer">
              Apply <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
