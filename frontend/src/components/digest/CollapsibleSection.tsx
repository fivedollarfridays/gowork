"use client";

import { type ReactNode, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { useTranslation } from "@/hooks/useTranslation";

interface CollapsibleSectionProps {
  id: string;
  title: string;
  count: number;
  defaultExpanded?: boolean;
  children: ReactNode;
}

/**
 * Shared collapsible wrapper for digest sections. Header is a button (keyboard-
 * accessible, aria-expanded); body toggles on click. Default-expanded when
 * ``count > 0``, collapsed when empty.
 */
export function CollapsibleSection({
  id,
  title,
  count,
  defaultExpanded,
  children,
}: CollapsibleSectionProps) {
  const { t } = useTranslation();
  const initial = defaultExpanded ?? count > 0;
  const [expanded, setExpanded] = useState(initial);
  const contentId = `digest-section-${id}-body`;
  const Icon = expanded ? ChevronDown : ChevronRight;
  const toggleLabel = expanded
    ? t("digest.collapse")
    : t("digest.expand");

  return (
    <Card>
      <CardContent className="p-4">
        <button
          type="button"
          aria-expanded={expanded}
          aria-controls={contentId}
          onClick={() => setExpanded((v) => !v)}
          className="flex w-full items-center justify-between gap-3 rounded text-left outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <span className="flex items-center gap-2">
            <Icon className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            <h2 className="text-lg font-semibold text-foreground">{title}</h2>
            {count > 0 && (
              <span
                aria-label={`${count} items`}
                className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary"
              >
                {count}
              </span>
            )}
          </span>
          <span className="sr-only">{toggleLabel}</span>
        </button>
        {expanded && (
          <div id={contentId} className="mt-3 text-sm text-foreground">
            {children}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
