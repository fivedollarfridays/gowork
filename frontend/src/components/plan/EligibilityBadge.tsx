import { Badge } from "@/components/ui/badge";
import { STATUS_BADGE_STYLES } from "@/lib/constants";
import { cn } from "@/lib/utils";

interface EligibilityBadgeProps {
  status?: "likely" | "check" | "unknown" | null;
}

export function EligibilityBadge({ status }: EligibilityBadgeProps) {
  if (!status) return null;

  if (status === "likely") {
    return (
      <Badge variant="outline" className={cn("text-xs rounded-full", STATUS_BADGE_STYLES.positive)}>
        Likely eligible
      </Badge>
    );
  }

  return (
    <Badge variant="outline" className={cn("text-xs rounded-full", STATUS_BADGE_STYLES.warning)}>
      Check eligibility
    </Badge>
  );
}
