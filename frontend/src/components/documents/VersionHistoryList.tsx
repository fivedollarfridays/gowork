"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  type DocType,
  type DocumentVersion,
  coverLetterPdfUrl,
  resumePdfUrl,
} from "@/lib/api/documents";

export interface VersionHistoryListProps {
  versions: DocumentVersion[];
  token: string;
  docType: DocType;
  emptyText: string;
  viewLabel: string;
  pdfLabel: string;
  generationBadgeLabels: Record<string, string>;
  onView?: (version: DocumentVersion) => void;
}

function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function pdfUrlFor(
  version: DocumentVersion,
  token: string,
): string {
  if (version.doc_type === "resume") {
    return resumePdfUrl(version.version_id, token);
  }
  return coverLetterPdfUrl(version.version_id, token);
}

/**
 * Newest-first list of document versions.
 *
 * Filters ``versions`` by ``docType`` — the parent typically passes the
 * full list and this component shows only the matching subset.
 *
 * The PDF button is an anchor with ``download`` so the browser saves the
 * PDF bytes returned by the backend (``application/pdf``) instead of
 * trying to render them inline (jsdom can't; real browsers can).
 */
export function VersionHistoryList({
  versions,
  token,
  docType,
  emptyText,
  viewLabel,
  pdfLabel,
  generationBadgeLabels,
  onView,
}: VersionHistoryListProps) {
  const filtered = versions.filter((v) => v.doc_type === docType);
  if (filtered.length === 0) {
    return (
      <p className="py-4 text-sm text-muted-foreground">{emptyText}</p>
    );
  }
  return (
    <ul className="space-y-2" aria-label="Document version history">
      {filtered.map((version) => {
        const badgeLabel =
          generationBadgeLabels[version.generation_method] ??
          version.generation_method;
        return (
          <li
            key={`${version.doc_type}-${version.version_id}`}
            className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-card p-3"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium">v{version.version_counter}</span>
              <Badge variant="secondary">{badgeLabel}</Badge>
              <span className="text-xs text-muted-foreground">
                {formatDate(version.created_at)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {onView && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => onView(version)}
                >
                  {viewLabel}
                </Button>
              )}
              <a
                className="inline-flex items-center rounded-md border border-border px-3 py-1 text-sm font-medium hover:bg-accent"
                href={pdfUrlFor(version, token)}
                download
                target="_blank"
                rel="noopener noreferrer"
              >
                {pdfLabel}
              </a>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
