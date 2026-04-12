"use client";

import { Phone, Calendar, AlertTriangle, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getTranslation, getLocale } from "@/lib/i18n";
import { toTelHref, humanizeLabel } from "@/lib/constants";

export interface SharedPlanData {
  session_id: string;
  created_at: string;
  barriers: string[];
  next_steps: string[];
  career_center_name: string;
  career_center_phone: string;
}

interface SharedPlanViewProps {
  plan: SharedPlanData | null;
}

function BarrierBadges({ barriers }: { barriers: string[] }) {
  return (
    <div className="flex flex-wrap gap-2">
      {barriers.map((b) => (
        <Badge key={b} variant="outline" className="text-xs">
          {humanizeLabel(b)}
        </Badge>
      ))}
    </div>
  );
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

export function SharedPlanView({ plan }: SharedPlanViewProps) {
  const locale = getLocale();
  const heading = getTranslation("share.heading", locale);
  const expired = getTranslation("share.expiredOrInvalid", locale);
  const generatedLabel = getTranslation("share.generatedOn", locale);

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

  return (
    <section className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-primary">{heading}</h1>
        <p className="text-sm text-muted-foreground flex items-center gap-1">
          <Calendar className="h-3 w-3" />
          {generatedLabel} {plan.created_at}
        </p>
      </div>

      {/* Barriers */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium">Barriers</CardTitle>
        </CardHeader>
        <CardContent>
          <BarrierBadges barriers={plan.barriers} />
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

      {/* Career Center */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium">Career Center</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm font-medium">{plan.career_center_name}</p>
          <a
            href={toTelHref(plan.career_center_phone)}
            className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
          >
            <Phone className="h-3 w-3" />
            {plan.career_center_phone}
          </a>
        </CardContent>
      </Card>
    </section>
  );
}
