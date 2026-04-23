"use client";

import { useTranslation } from "@/hooks/useTranslation";
import { CollapsibleSection } from "./CollapsibleSection";
import { DigestSectionBody } from "./DigestSectionBody";

interface DigestYesterdaySectionProps {
  body: string;
  count: number;
}

export function DigestYesterdaySection({
  body,
  count,
}: DigestYesterdaySectionProps) {
  const { t } = useTranslation();
  return (
    <CollapsibleSection
      id="yesterday"
      title={t("digest.sections.yesterday.title")}
      count={count}
    >
      <DigestSectionBody
        body={body}
        emptyPlaceholder={t("digest.sections.empty.placeholder")}
      />
    </CollapsibleSection>
  );
}
