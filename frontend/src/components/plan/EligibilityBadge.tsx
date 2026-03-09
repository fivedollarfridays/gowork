interface EligibilityBadgeProps {
  status?: "likely" | "check" | null;
}

export function EligibilityBadge({ status }: EligibilityBadgeProps) {
  if (!status) return null;

  if (status === "likely") {
    return (
      <span className="inline-flex items-center rounded-full bg-success/10 px-2 py-0.5 text-xs font-medium text-success">
        Likely eligible
      </span>
    );
  }

  return (
    <span className="inline-flex items-center rounded-full bg-warning/10 px-2 py-0.5 text-xs font-medium text-warning-foreground">
      Check eligibility
    </span>
  );
}
