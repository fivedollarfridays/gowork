"use client";

import { useTranslation } from "@/hooks/useTranslation";
import { CollapsibleSection } from "./CollapsibleSection";
import { DigestSectionBody } from "./DigestSectionBody";

interface DigestWeekSectionProps {
  body: string;
  count: number;
}

export function DigestWeekSection({ body, count }: DigestWeekSectionProps) {
  const { t } = useTranslation();
  return (
    <CollapsibleSection
      id="week"
      title={t("digest.sections.week.title")}
      count={count}
      defaultExpanded={true}
    >
      {count === 0 ? (
        <p className="text-muted-foreground italic">
          {t("digest.sections.week.coming_soon")}
        </p>
      ) : (
        <DigestSectionBody
          body={body}
          emptyPlaceholder={t("digest.sections.empty.placeholder")}
        />
      )}
    </CollapsibleSection>
  );
}
