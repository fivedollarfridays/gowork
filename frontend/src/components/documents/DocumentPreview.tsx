"use client";

export interface DocumentPreviewProps {
  markdown: string | null;
  emptyText: string;
  ariaLabel?: string;
}

/**
 * Minimal markdown preview — renders the raw markdown in a ``<pre>``
 * element so we don't add a new heavy dependency. This is v1; a richer
 * renderer can be swapped in later without changing the call sites.
 */
export function DocumentPreview({
  markdown,
  emptyText,
  ariaLabel,
}: DocumentPreviewProps) {
  if (!markdown) {
    return (
      <div
        className="rounded-md border border-dashed border-border p-6 text-center text-sm text-muted-foreground"
        role="region"
        aria-label={ariaLabel}
      >
        {emptyText}
      </div>
    );
  }
  return (
    <div
      className="rounded-md border border-border bg-card p-4"
      role="region"
      aria-label={ariaLabel}
    >
      <pre
        data-testid="document-preview-body"
        className="whitespace-pre-wrap break-words font-sans text-sm leading-relaxed"
      >
        {markdown}
      </pre>
    </div>
  );
}
