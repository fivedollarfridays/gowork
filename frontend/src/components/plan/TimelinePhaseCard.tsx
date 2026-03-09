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
  ExternalLink,
  type LucideIcon,
} from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toTelHref, mapsUrl, CAREER_CENTER } from "@/lib/constants";
import type { TimelinePhase, ActionCategory, ActionItem } from "@/lib/types";

/* ── Action link mapping ─────────────────────────────────────────────── */

interface ActionLink { label: string; url: string }

const BENEFIT_URLS: Record<string, string> = {
  snap: "https://www.alabamabenefits.gov/",
  tanf: "https://www.alabamabenefits.gov/",
  medicaid: "https://www.alabamabenefits.gov/",
  all_kids: "https://www.alabamabenefits.gov/allkids/",
  childcare_subsidy: "https://dhr.alabama.gov/child-care/",
  section_8: "https://www.hamd.org/housing-choice-voucher-program/",
  liheap: "https://adeca.alabama.gov/liheap/",
  wic: "https://www.alabamapublichealth.gov/wic/",
};

function getActionLink(action: ActionItem): ActionLink | null {
  const t = action.title.toLowerCase();

  // Career Center → Google Maps
  if (action.category === "career_center" && t.includes("visit")) {
    return { label: "Visit", url: mapsUrl(CAREER_CENTER.address) };
  }

  // Job applications → Alabama JobLink
  if (action.category === "job_application" && t.startsWith("apply")) {
    return { label: "Apply", url: "https://joblink.alabama.gov/" };
  }

  // Benefits enrollment — match program name in title
  if (action.category === "benefits_enrollment") {
    for (const [prog, url] of Object.entries(BENEFIT_URLS)) {
      if (t.includes(prog.toLowerCase().replace("_", " ")) || t.includes(prog.toLowerCase())) {
        return { label: "Apply", url };
      }
    }
    if (t.includes("benefit")) {
      return { label: "Apply", url: "https://www.alabamabenefits.gov/" };
    }
  }

  // WIOA / Training
  if (action.category === "training") {
    if (t.includes("wioa")) return { label: "Enroll", url: "https://www.careeronestop.org/LocalHelp/AmericanJobCenters/find-american-job-centers.aspx" };
    return { label: "Enroll", url: mapsUrl(CAREER_CENTER.address) };
  }

  // Criminal record
  if (action.category === "criminal_record") {
    if (t.includes("legal services")) return { label: "Contact", url: "https://www.legalservicesalabama.org/" };
    if (t.includes("expungement")) return { label: "Learn More", url: "https://www.legalservicesalabama.org/get-legal-help.html" };
  }

  // Credit repair
  if (action.category === "credit_repair") {
    if (t.includes("annualcreditreport")) return { label: "Visit", url: "https://www.annualcreditreport.com/" };
    if (t.includes("greenpath")) return { label: "Visit", url: "https://www.greenpath.com/" };
    if (t.includes("credit report") || t.includes("credit dispute")) return { label: "Visit", url: "https://www.annualcreditreport.com/" };
  }

  // Housing
  if (action.category === "housing") {
    return { label: "Apply", url: "https://www.hamd.org/" };
  }

  // Childcare
  if (action.category === "childcare") {
    return { label: "Apply", url: "https://dhr.alabama.gov/child-care/" };
  }

  return null;
}

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
  const link = getActionLink(action);
  const [expanded, setExpanded] = useState(false);
  const hasDetails = !!(action.detail || action.resource_name || action.resource_phone);

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
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium">{action.title}</p>
          {link && (
            <a
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="inline-flex items-center gap-1 shrink-0 rounded-full bg-secondary/10 px-2.5 py-0.5 text-[11px] font-semibold text-secondary hover:bg-secondary/20 transition-colors"
            >
              {link.label}
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
          {hasDetails && (
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="shrink-0 ml-auto"
              aria-expanded={expanded}
              aria-label={expanded ? "Hide details" : "Show details"}
            >
              <ChevronDown className={`h-3.5 w-3.5 text-muted-foreground transition-transform duration-200 ${expanded ? "rotate-180" : ""}`} />
            </button>
          )}
        </div>

        <div
          className={`grid transition-[grid-template-rows] duration-200 ease-out ${expanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]"}`}
        >
          <div className="overflow-hidden">
            <div className="pt-1 space-y-0.5">
              {action.detail && (
                <p className="text-xs text-muted-foreground">{action.detail}</p>
              )}
              {action.resource_name && (
                <p className="text-xs text-muted-foreground">{action.resource_name}</p>
              )}
              {action.resource_phone && (
                <a
                  href={toTelHref(action.resource_phone)}
                  className="text-xs text-primary underline block"
                >
                  {action.resource_phone}
                </a>
              )}
            </div>
          </div>
        </div>
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
