"use client";

import { Badge } from "@/components/ui/badge";
import type { EvidenceSource } from "@/lib/types";

interface EvidenceChipsProps {
  evidence?: EvidenceSource[];
}

export function EvidenceChips({ evidence }: EvidenceChipsProps) {
  if (!evidence || evidence.length === 0) return null;

  return (
    <div className="mt-2" aria-label="Source evidence">
      <span className="text-xs font-medium text-muted-foreground">Sources</span>
      <div className="mt-1 flex flex-wrap gap-1">
        {evidence.map((source, i) => (
          <Badge key={`${source.name}-${i}`} variant="secondary" className="text-xs">
            {source.name}
          </Badge>
        ))}
      </div>
    </div>
  );
}
