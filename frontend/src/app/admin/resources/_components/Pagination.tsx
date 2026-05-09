"use client";

/**
 * Pagination controls for /admin/resources: prev/next buttons and a
 * "Page X of Y • N total" indicator. Page-size is fixed at the
 * caller's discretion (T26.8 uses PAGE_SIZE=50).
 */

import { Button } from "@/components/ui/button";

export function Pagination({
  offset,
  total,
  pageSize,
  onPrev,
  onNext,
}: {
  offset: number;
  total: number;
  pageSize: number;
  onPrev: () => void;
  onNext: () => void;
}) {
  const pageNum = Math.floor(offset / pageSize) + 1;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="flex items-center justify-between text-sm text-muted-foreground">
      <span>
        Page {pageNum} of {totalPages} • {total} total
      </span>
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onPrev}
          disabled={offset <= 0}
        >
          Prev
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onNext}
          disabled={offset + pageSize >= total}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
