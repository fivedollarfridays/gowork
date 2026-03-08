interface EvidenceChipsProps {
  sources: string[];
}

export function EvidenceChips({ sources }: EvidenceChipsProps) {
  if (sources.length === 0) return <></>;
  return (
    <div className="flex flex-wrap gap-1">
      {sources.map((src) => (
        <span
          key={src}
          className="rounded bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
        >
          {src}
        </span>
      ))}
    </div>
  );
}
