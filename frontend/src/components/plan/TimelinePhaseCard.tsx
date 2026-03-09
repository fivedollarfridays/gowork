"use client";

import { useState } from "react";
import {
  ChevronDown,
  Briefcase,
  ClipboardList,
  CreditCard,
  Scale,
  GraduationCap,
  Building2,
  Home,
  Baby,
  type LucideIcon,
} from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toTelHref } from "@/lib/constants";
import type { TimelinePhase, ActionCategory, ActionItem } from "@/lib/types";

const CATEGORY_ICONS: Record<ActionCategory, LucideIcon> = {
  job_application: Briefcase,
  benefits_enrollment: ClipboardList,
  credit_repair: CreditCard,
  criminal_record: Scale,
  training: GraduationCap,
  career_center: Building2,
  housing: Home,
  childcare: Baby,
};

interface TimelinePhaseCardProps {
  phase: TimelinePhase;
  dateRange: string;
  defaultOpen?: boolean;
  checklist?: Record<string, boolean>;
  onToggle?: (key: string, completed: boolean) => void;
}

interface ActionRowProps {
  action: ActionItem;
  actionKey?: string;
  checked?: boolean;
  onToggle?: (key: string, completed: boolean) => void;
}

function ActionRow({ action, actionKey, checked, onToggle }: ActionRowProps) {
  const Icon = CATEGORY_ICONS[action.category] ?? Building2;

  return (
    <li className="flex items-start gap-3 py-2">
      {actionKey != null && onToggle && (
        <input
          type="checkbox"
          checked={checked ?? false}
          onChange={(e) => onToggle(actionKey, e.target.checked)}
          className="mt-0.5 shrink-0"
          aria-label={`Mark "${action.title}" complete`}
        />
      )}
      <Icon className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" aria-hidden="true" />
      <div className="min-w-0 space-y-0.5">
        <p className="text-sm font-medium">{action.title}</p>
        {action.detail && (
          <p className="text-xs text-muted-foreground">{action.detail}</p>
        )}
        {action.resource_name && (
          <p className="text-xs text-muted-foreground">{action.resource_name}</p>
        )}
        {action.resource_phone && (
          <a
            href={toTelHref(action.resource_phone)}
            className="text-xs text-primary underline"
          >
            {action.resource_phone}
          </a>
        )}
      </div>
    </li>
  );
}

export function TimelinePhaseCard({ phase, dateRange, defaultOpen = false, checklist, onToggle }: TimelinePhaseCardProps) {
  const [open, setOpen] = useState(defaultOpen);
  const count = phase.actions.length;
  const countLabel = count === 1 ? "1 action" : `${count} actions`;

  return (
    <Card>
      <CardHeader className="pb-0">
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="flex w-full items-center justify-between gap-2 text-left"
          aria-expanded={open}
          aria-label={`${phase.label} — ${dateRange}`}
        >
          <div className="flex items-center gap-2 min-w-0">
            <span className="font-semibold text-base">{phase.label}</span>
            <span className="text-sm text-muted-foreground">{dateRange}</span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Badge variant="outline" className="text-xs">{countLabel}</Badge>
            <ChevronDown
              className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`}
              aria-hidden="true"
            />
          </div>
        </button>
      </CardHeader>
      {open && (
        <CardContent className="pt-2">
          <ul className="divide-y">
            {phase.actions.map((action, i) => {
              const key = `${phase.phase_id}:${i}`;
              return (
                <ActionRow
                  key={key}
                  action={action}
                  actionKey={checklist != null ? key : undefined}
                  checked={checklist?.[key]}
                  onToggle={onToggle}
                />
              );
            })}
          </ul>
        </CardContent>
      )}
    </Card>
  );
}
