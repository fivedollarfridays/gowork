"use client";

import { useTranslation } from "@/hooks/useTranslation";
import { CollapsibleSection } from "./CollapsibleSection";
import { DigestSectionBody } from "./DigestSectionBody";

interface DigestTodaySectionProps {
  body: string;
  count: number;
}

export function DigestTodaySection({ body, count }: DigestTodaySectionProps) {
  const { t } = useTranslation();
  return (
    <CollapsibleSection
      id="today"
      title={t("digest.sections.today.title")}
      count={count}
    >
      <DigestSectionBody
        body={body}
        emptyPlaceholder={t("digest.sections.empty.placeholder")}
      />
    </CollapsibleSection>
  );
}
