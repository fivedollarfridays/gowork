"use client";

import type { LucideIcon } from "lucide-react";
import { m } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useHaptic } from "@/hooks/useHaptic";
import type { BarrierType, EmploymentStatus } from "@/lib/types";
import { BARRIER_ICONS, barrierCountToSeverity } from "@/lib/constants";

interface BarrierOption {
  key: BarrierType;
  label: string;
  description: string;
  icon: LucideIcon;
}

const BARRIER_OPTIONS: BarrierOption[] = [
  { key: "credit", label: "Credit / Financial", description: "Credit history affecting job eligibility", icon: BARRIER_ICONS.credit },
  { key: "transportation", label: "Transportation", description: "No vehicle or limited bus access", icon: BARRIER_ICONS.transportation },
  { key: "childcare", label: "Childcare", description: "Need childcare to attend work or training", icon: BARRIER_ICONS.childcare },
  { key: "housing", label: "Housing", description: "Unstable housing or facing eviction", icon: BARRIER_ICONS.housing },
  { key: "health", label: "Health", description: "Physical or mental health challenges", icon: BARRIER_ICONS.health },
  { key: "training", label: "Training / Certification", description: "Need skills training or license renewal", icon: BARRIER_ICONS.training },
  { key: "criminal_record", label: "Criminal Record", description: "Background check concerns", icon: BARRIER_ICONS.criminal_record },
];

const SEVERITY_VARIANT: Record<string, "default" | "secondary" | "destructive"> = {
  high: "destructive",
  medium: "secondary",
  low: "default",
};

export interface BarrierFormData {
  zipCode: string;
  employment: EmploymentStatus;
  barriers: Record<BarrierType, boolean>;
  workHistory: string;
  hasVehicle: boolean;
  availableHours: import("@/lib/types").AvailableHours;
}

interface BarrierFormProps {
  data: BarrierFormData;
  onChange: (data: BarrierFormData) => void;
}

export function BarrierForm({ data, onChange }: BarrierFormProps) {
  const selectedCount = Object.values(data.barriers).filter(Boolean).length;
  const severity = barrierCountToSeverity(selectedCount);
  const severityVariant = SEVERITY_VARIANT[severity] ?? "default";
  const haptic = useHaptic();

  function toggleBarrier(key: BarrierType) {
    haptic.tap();
    onChange({
      ...data,
      barriers: { ...data.barriers, [key]: !data.barriers[key] },
    });
  }

  return (
    <div className="space-y-6">
      {/* Severity preview */}
      {selectedCount > 0 && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Barrier severity:</span>
          <Badge variant={severityVariant} className="capitalize">{severity} ({selectedCount})</Badge>
        </div>
      )}

      {/* Barrier grid */}
      <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
        {BARRIER_OPTIONS.map((opt) => {
          const checked = !!data.barriers[opt.key];
          const Icon = opt.icon;
          return (
            <m.div key={opt.key} whileTap={{ scale: 0.97 }}>
              <Card
                role="button"
                tabIndex={0}
                onClick={() => toggleBarrier(opt.key)}
                onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggleBarrier(opt.key); } }}
                className={cn(
                  "cursor-pointer p-4 transition-colors",
                  checked
                    ? "border-secondary bg-secondary/5 ring-2 ring-secondary/50"
                    : "hover:border-muted-foreground/30"
                )}
              >
                <div className="flex items-start gap-3">
                  <Checkbox
                    checked={checked}
                    onCheckedChange={() => toggleBarrier(opt.key)}
                    onClick={(e) => e.stopPropagation()}
                    className="mt-0.5"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <Icon className={cn("h-4 w-4 shrink-0", checked ? "text-secondary" : "text-muted-foreground")} />
                      <span className="text-sm font-medium">{opt.label}</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">{opt.description}</p>
                  </div>
                </div>
              </Card>
            </m.div>
          );
        })}
      </div>
    </div>
  );
}
