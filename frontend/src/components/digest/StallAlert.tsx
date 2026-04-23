"use client";

import Link from "next/link";
import { AlertTriangle } from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";
import { CollapsibleSection } from "./CollapsibleSection";
import { DigestSectionBody } from "./DigestSectionBody";

interface StallAlertProps {
  body: string;
  count: number;
  /** Deep-link href for the navigator CTA. Defaults to /plan when sessionId provided. */
  barrierHref?: string;
}

export function StallAlert({ body, count, barrierHref }: StallAlertProps) {
  const { t } = useTranslation();
  return (
    <CollapsibleSection
      id="stall"
      title={t("digest.sections.stall.title")}
      count={count}
    >
      <div className="space-y-3">
        <div className="flex items-start gap-2 rounded border border-warning bg-warning/10 p-3 text-warning-foreground">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <div className="flex-1">
            <DigestSectionBody
              body={body}
              emptyPlaceholder={t("digest.sections.empty.placeholder")}
            />
          </div>
        </div>
        <Link
          href={barrierHref ?? "/plan"}
          className="inline-flex items-center text-sm font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          {t("digest.sections.stall.cta")}
        </Link>
      </div>
    </CollapsibleSection>
  );
}
