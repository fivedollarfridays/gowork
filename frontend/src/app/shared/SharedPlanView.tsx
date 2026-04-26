"use client";

import { Phone, Calendar, AlertTriangle, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getTranslation, getLocale, type Locale } from "@/lib/i18n";
import { toTelHref } from "@/lib/constants";

/**
 * Shape of the public ``GET /api/plan/shared/{token}`` payload.
 *
 * Note: the backend deliberately strips PII (T13.71 P1) — there is no
 * ``session_id`` and no raw ``barriers`` slug list. ``barriers_count`` is a
 * non-identifying scalar that lets us show "this person is working on N
 * things" without disclosing protected categories.
 */
export interface SharedPlanData {
  created_at: string;
  barriers_count: number;
  next_steps: string[];
  career_center_name: string;
  career_center_phone: string;
}

interface SharedPlanViewProps {
  plan: SharedPlanData | null;
}

function NextStepsList({ steps }: { steps: string[] }) {
  return (
    <ul className="space-y-2">
      {steps.map((step, i) => (
        <li key={i} className="flex items-start gap-2 text-sm">
          <CheckCircle2 className="h-4 w-4 text-success mt-0.5 shrink-0" />
          {step}
        </li>
      ))}
    </ul>
  );
}

function formatGeneratedAt(value: string): string {
  // The backend returns an ISO timestamp with microseconds; format to a
  // human date so we don't render "...T22:12:50.762313+00:00" raw.
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleDateString();
}

function barriersCountLabel(count: number, locale: Locale): string {
  if (count <= 0) return getTranslation("share.barriersZero", locale);
  if (count === 1) return getTranslation("share.barriersOne", locale);
  return getTranslation("share.barriersMany", locale).replace(
    "{{count}}",
    String(count),
  );
}

export function SharedPlanView({ plan }: SharedPlanViewProps) {
  const locale = getLocale();
  const heading = getTranslation("share.heading", locale);
  const expired = getTranslation("share.expiredOrInvalid", locale);
  const generatedLabel = getTranslation("share.generatedOn", locale);
  const focusAreasTitle = getTranslation("share.focusAreasTitle", locale);
  const careerCenterTitle = getTranslation("share.careerCenterTitle", locale);

  if (!plan) {
    return (
      <section className="flex items-center justify-center min-h-[50vh] px-4">
        <Card className="max-w-md w-full">
          <CardContent className="py-8 text-center space-y-3">
            <AlertTriangle className="h-8 w-8 text-warning mx-auto" />
            <p className="text-sm text-muted-foreground">{expired}</p>
          </CardContent>
        </Card>
      </section>
    );
  }

  const phone = plan.career_center_phone?.trim() ?? "";
  const centerName = plan.career_center_name?.trim() ?? "";
  const hasCenter = centerName.length > 0 || phone.length > 0;

  return (
    <section className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-primary">{heading}</h1>
        <p className="text-sm text-muted-foreground flex items-center gap-1">
          <Calendar className="h-3 w-3" />
          {generatedLabel} {formatGeneratedAt(plan.created_at)}
        </p>
      </div>

      {/* Barriers — public-safe count only (T13.71 P1) */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium">{focusAreasTitle}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {barriersCountLabel(plan.barriers_count ?? 0, locale)}
          </p>
        </CardContent>
      </Card>

      {/* Next Steps */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium">Next Steps</CardTitle>
        </CardHeader>
        <CardContent>
          <NextStepsList steps={plan.next_steps} />
        </CardContent>
      </Card>

      {/* Career Center — only render the phone link when we have a number */}
      {hasCenter && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-medium">{careerCenterTitle}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {centerName && (
              <p className="text-sm font-medium">{centerName}</p>
            )}
            {phone && (
              <a
                href={toTelHref(phone)}
                className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
              >
                <Phone className="h-3 w-3" />
                {phone}
              </a>
            )}
          </CardContent>
        </Card>
      )}
    </section>
  );
}
