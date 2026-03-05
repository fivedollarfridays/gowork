import {
  CreditCard,
  Bus,
  Baby,
  Home,
  Heart,
  GraduationCap,
  Shield,
  type LucideIcon,
} from "lucide-react";
import type { BarrierSeverity, BarrierType, EmploymentStatus } from "./types";

export const MONTGOMERY_ZIP_REGEX = /^361\d{2}$/;

export function isValidMontgomeryZip(zip: string): boolean {
  return MONTGOMERY_ZIP_REGEX.test(zip);
}

export function barrierCountToSeverity(count: number): BarrierSeverity {
  if (count >= 3) return "high";
  if (count === 2) return "medium";
  return "low";
}

export function humanizeLabel(s: string): string {
  return s.replaceAll("_", " ");
}

export function safeHref(url: string): string | undefined {
  try {
    const parsed = new URL(url, "https://placeholder.invalid");
    return parsed.protocol === "https:" || parsed.protocol === "http:" ? url : undefined;
  } catch {
    return undefined;
  }
}

export const EMPLOYMENT_OPTIONS: { value: EmploymentStatus; label: string }[] = [
  { value: "unemployed", label: "Unemployed" },
  { value: "underemployed", label: "Underemployed" },
  { value: "seeking_change", label: "Seeking a career change" },
];

export const BARRIER_ICONS: Record<BarrierType, LucideIcon> = {
  credit: CreditCard,
  transportation: Bus,
  childcare: Baby,
  housing: Home,
  health: Heart,
  training: GraduationCap,
  criminal_record: Shield,
};

export const STATUS_BADGE_STYLES = {
  positive: "bg-green-100 text-green-700 border-green-200",
  warning: "bg-amber-100 text-amber-700 border-amber-200",
  negative: "bg-red-100 text-red-700 border-red-200",
} as const;

export const SEVERITY_BADGE_STYLES: Record<BarrierSeverity, string> = {
  low: STATUS_BADGE_STYLES.positive,
  medium: STATUS_BADGE_STYLES.warning,
  high: STATUS_BADGE_STYLES.negative,
};
