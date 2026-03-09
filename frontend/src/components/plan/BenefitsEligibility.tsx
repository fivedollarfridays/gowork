"use client";

import { useState } from "react";
import { ChevronDown, ExternalLink, MapPin, Phone } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PROGRAM_LABELS, STATUS_BADGE_STYLES, formatDollar, mapsUrl, safeHref, toTelHref } from "@/lib/constants";
import type { BenefitsEligibility as BenefitsEligibilityType, ProgramEligibility } from "@/lib/types";

interface BenefitsEligibilityProps {
  eligibility: BenefitsEligibilityType | null | undefined;
  enrolledPrograms?: string[];
}

const CONFIDENCE_STYLES: Record<string, { label: string; style: string }> = {
  likely: { label: "Likely eligible", style: STATUS_BADGE_STYLES.positive },
  possible: { label: "Possibly eligible", style: STATUS_BADGE_STYLES.warning },
  unlikely: { label: "Unlikely", style: STATUS_BADGE_STYLES.negative },
};

function ProgramRow({ program, defaultOpen }: { program: ProgramEligibility; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen ?? false);
  const label = PROGRAM_LABELS[program.program] ?? program.program;
  const conf = CONFIDENCE_STYLES[program.confidence] ?? CONFIDENCE_STYLES.unlikely;
  const info = program.application_info;

  return (
    <div className="border rounded-lg p-4 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-medium">{label}</span>
          <Badge
            variant="outline"
            className={`text-xs shrink-0 ${conf.style}`}
            aria-label={`${label}: ${conf.label}`}
          >
            {conf.label}
          </Badge>
        </div>
        <span className="font-semibold text-sm whitespace-nowrap">
          {formatDollar(program.estimated_monthly_value)}/mo
        </span>
      </div>

      <p className="text-xs text-muted-foreground">
        {formatDollar(program.income_headroom)} below threshold
      </p>

      {info && (
        <>
          <button
            type="button"
            onClick={() => setOpen(!open)}
            className="flex items-center gap-1 text-xs text-primary hover:underline"
            aria-expanded={open}
          >
            <ChevronDown className={`h-3 w-3 transition-transform ${open ? "rotate-180" : ""}`} />
            How to apply
          </button>

          {open && (
            <div className="text-sm space-y-3 pt-1 pl-4 border-l-2 border-primary/20">
              <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
                {info.application_steps.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>

              <div className="space-y-1 text-xs text-muted-foreground">
                <p className="font-medium text-foreground">{info.office_name}</p>
                <p className="flex items-center gap-1">
                  <MapPin className="h-3 w-3 shrink-0" aria-hidden="true" />
                  <a href={mapsUrl(info.office_address)} target="_blank" rel="noopener noreferrer" className="underline">
                    {info.office_address}
                  </a>
                </p>
                <p className="flex items-center gap-1">
                  <Phone className="h-3 w-3 shrink-0" aria-hidden="true" />
                  <a href={toTelHref(info.office_phone)} className="underline">{info.office_phone}</a>
                </p>
                <p className="text-muted-foreground">Processing: {info.processing_time}</p>
              </div>

              <div>
                <p className="text-xs font-medium">Required documents:</p>
                <ul className="list-disc list-inside text-xs text-muted-foreground">
                  {info.required_documents.map((doc, i) => (
                    <li key={i}>{doc}</li>
                  ))}
                </ul>
              </div>

              {safeHref(info.application_url) && (
                <a
                  href={safeHref(info.application_url)!}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                >
                  Apply online <ExternalLink className="h-3 w-3" aria-hidden="true" />
                </a>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export function BenefitsEligibility({ eligibility, enrolledPrograms = [] }: BenefitsEligibilityProps) {
  if (!eligibility) return null;

  const enrolled = new Set(enrolledPrograms);
  const enrolledProgList = eligibility.eligible_programs.filter((p) => enrolled.has(p.program));
  const additionalProgList = eligibility.eligible_programs.filter((p) => !enrolled.has(p.program));
  const hasEnrolled = enrolledProgList.length > 0;
  const hasAdditional = additionalProgList.length > 0;

  return (
    <section aria-label="Benefits eligibility" className="space-y-4">
      <h2 className="text-xl font-semibold text-primary">Benefits You May Qualify For</h2>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center justify-between">
            <span>{eligibility.eligible_programs.length} programs</span>
            <span className="text-success font-bold">{formatDollar(eligibility.total_estimated_monthly)}/mo estimated</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {hasEnrolled && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">Currently enrolled</p>
              {enrolledProgList.map((p) => (
                <ProgramRow key={p.program} program={p} />
              ))}
            </div>
          )}

          {hasAdditional && (
            <div className="space-y-2">
              {hasEnrolled && (
                <p className="text-sm font-medium text-muted-foreground">You may also qualify for</p>
              )}
              {additionalProgList.map((p) => (
                <ProgramRow key={p.program} program={p} />
              ))}
            </div>
          )}

          <p className="text-xs text-muted-foreground italic pt-2">
            {eligibility.disclaimer}
          </p>
        </CardContent>
      </Card>
    </section>
  );
}
