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
  positive: "bg-success/10 text-success border-success/20",
  warning: "bg-warning/10 text-warning-foreground border-warning/20",
  negative: "bg-destructive/10 text-destructive border-destructive/20",
} as const;

export const SEVERITY_BADGE_STYLES: Record<BarrierSeverity, string> = {
  low: STATUS_BADGE_STYLES.positive,
  medium: STATUS_BADGE_STYLES.warning,
  high: STATUS_BADGE_STYLES.negative,
};

export function daysToMonths(days: number): string {
  if (days <= 30) return `${days} days`;
  const months = Math.round(days / 30);
  return `~${months} month${months === 1 ? "" : "s"}`;
}

export const CAREER_CENTER = {
  name: "Montgomery Career Center",
  address: "1060 East South Boulevard, Montgomery, AL 36116",
  phone: "334-286-1746",
  hours: "Monday \u2013 Friday, 8:00 AM \u2013 5:00 PM",
} as const;

export const INDUSTRY_OPTIONS = [
  { value: "healthcare", label: "Healthcare" },
  { value: "manufacturing", label: "Manufacturing" },
  { value: "food_service", label: "Food Service" },
  { value: "government", label: "Government" },
  { value: "retail", label: "Retail" },
  { value: "construction", label: "Construction" },
  { value: "transportation", label: "Transportation" },
] as const;

export const CERTIFICATION_OPTIONS = [
  { value: "CNA", label: "CNA (Certified Nursing Assistant)" },
  { value: "CDL", label: "CDL (Commercial Driver's License)" },
  { value: "LPN", label: "LPN (Licensed Practical Nurse)" },
] as const;

export const READINESS_BAND_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  not_ready: { bg: "bg-destructive/10", text: "text-destructive", border: "border-destructive/20" },
  developing: { bg: "bg-warning/10", text: "text-warning-foreground", border: "border-warning/20" },
  ready: { bg: "bg-success/10", text: "text-success", border: "border-success/20" },
  strong: { bg: "bg-primary/10", text: "text-primary", border: "border-primary/20" },
};

/** Hex colors for PDF inline styles (html2pdf.js can't use CSS vars). */
export const PDF_SEVERITY_COLORS: Record<string, { bg: string; text: string }> = {
  low: { bg: "#dcfce7", text: "#166534" },
  medium: { bg: "#fef9c3", text: "#854d0e" },
  high: { bg: "#fee2e2", text: "#991b1b" },
};
