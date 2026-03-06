"use client";

import { useState, useCallback } from "react";
import {
  Bus,
  ChevronDown,
  ChevronUp,
  MapPin,
  Phone,
  ThumbsUp,
  ThumbsDown,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import type { BarrierCard as BarrierCardType } from "@/lib/types";
import { BARRIER_ICONS, SEVERITY_BADGE_STYLES, humanizeLabel } from "@/lib/constants";
import { submitResourceFeedback } from "@/lib/api";

const INITIAL_RESOURCE_COUNT = 2;

type FeedbackState = Record<number, boolean | null>;

function loadFeedbackState(sessionId: string, resourceIds: number[]): FeedbackState {
  if (typeof window === "undefined") return {};
  const state: FeedbackState = {};
  for (const id of resourceIds) {
    const stored = sessionStorage.getItem(`feedback_${sessionId}_${id}`);
    state[id] = stored === "true" ? true : stored === "false" ? false : null;
  }
  return state;
}

interface BarrierCardViewProps {
  barrier: BarrierCardType;
  sessionId?: string;
}

export function BarrierCardView({ barrier, sessionId }: BarrierCardViewProps) {
  const [expanded, setExpanded] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackState>(() =>
    sessionId ? loadFeedbackState(sessionId, barrier.resources.map((r) => r.id)) : {},
  );

  const handleFeedback = useCallback(
    (resourceId: number, helpful: boolean) => {
      if (!sessionId) return;

      setFeedback((prev) => {
        const current = prev[resourceId];
        const newValue = current === helpful ? null : helpful;

        if (newValue === null) {
          sessionStorage.removeItem(`feedback_${sessionId}_${resourceId}`);
        } else {
          sessionStorage.setItem(`feedback_${sessionId}_${resourceId}`, String(newValue));
          submitResourceFeedback({
            resource_id: resourceId,
            session_id: sessionId,
            helpful: newValue,
          }).catch(() => {});
        }

        return { ...prev, [resourceId]: newValue };
      });
    },
    [sessionId],
  );
  const Icon = BARRIER_ICONS[barrier.type];
  const badgeStyle = SEVERITY_BADGE_STYLES[barrier.severity] ?? SEVERITY_BADGE_STYLES.low;
  const hasMoreResources = barrier.resources.length > INITIAL_RESOURCE_COUNT;
  const visibleResources = expanded ? barrier.resources : barrier.resources.slice(0, INITIAL_RESOURCE_COUNT);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
              <Icon className="h-5 w-5 text-foreground/70" />
            </div>
            <CardTitle className="text-base">{barrier.title}</CardTitle>
          </div>
          <Badge className={cn("capitalize", badgeStyle)} variant="outline">
            {barrier.severity}
          </Badge>
        </div>
        {barrier.timeline_days && (
          <p className="text-xs text-muted-foreground ml-12">
            Estimated timeline: ~{barrier.timeline_days} days
          </p>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Action steps */}
        {barrier.actions.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Action Steps</h4>
            <ol className="list-decimal list-inside space-y-1.5 text-sm text-muted-foreground">
              {barrier.actions.map((action, i) => (
                <li key={i}>{action}</li>
              ))}
            </ol>
          </div>
        )}

        {/* Matched resources */}
        {barrier.resources.length > 0 && (
          <>
            <Separator />
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Matched Resources</h4>
              <ul className="space-y-2">
                {visibleResources.map((resource) => (
                  <li key={resource.id} className="flex items-start gap-3 text-sm">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium">{resource.name}</span>
                        <Badge variant="outline" className="text-xs">
                          {humanizeLabel(resource.category)}
                        </Badge>
                      </div>
                      {resource.address && (
                        <a
                          href={`https://maps.google.com/?q=${encodeURIComponent(resource.address)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 mt-1 text-xs text-muted-foreground hover:text-secondary hover:underline"
                        >
                          <MapPin className="h-3 w-3 shrink-0" />
                          {resource.address}
                        </a>
                      )}
                      {resource.phone && (
                        <a
                          href={`tel:${resource.phone}`}
                          className="flex items-center gap-1 mt-0.5 text-xs text-muted-foreground hover:text-secondary hover:underline"
                        >
                          <Phone className="h-3 w-3 shrink-0" />
                          {resource.phone}
                        </a>
                      )}
                    </div>
                    {sessionId && (
                      <div className="flex shrink-0 gap-1">
                        <button
                          type="button"
                          aria-label="Mark as helpful"
                          data-active={feedback[resource.id] === true ? "true" : undefined}
                          onClick={() => handleFeedback(resource.id, true)}
                          className={cn(
                            "rounded p-1 transition-colors",
                            feedback[resource.id] === true
                              ? "text-success"
                              : "text-muted-foreground/50 hover:text-success",
                          )}
                        >
                          <ThumbsUp className="h-3.5 w-3.5" />
                        </button>
                        <button
                          type="button"
                          aria-label="Mark as not helpful"
                          data-active={feedback[resource.id] === false ? "true" : undefined}
                          onClick={() => handleFeedback(resource.id, false)}
                          className={cn(
                            "rounded p-1 transition-colors",
                            feedback[resource.id] === false
                              ? "text-muted-foreground"
                              : "text-muted-foreground/50 hover:text-muted-foreground",
                          )}
                        >
                          <ThumbsDown className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
              {hasMoreResources && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setExpanded(!expanded)}
                  className="text-xs h-7 px-2"
                >
                  {expanded ? (
                    <>Show less <ChevronUp className="h-3 w-3 ml-1" /></>
                  ) : (
                    <>+{barrier.resources.length - INITIAL_RESOURCE_COUNT} more <ChevronDown className="h-3 w-3 ml-1" /></>
                  )}
                </Button>
              )}
            </div>
          </>
        )}

        {/* Transit matches */}
        {barrier.transit_matches.length > 0 && (
          <>
            <Separator />
            <div className="space-y-1.5">
              <h4 className="text-sm font-medium flex items-center gap-1.5">
                <Bus className="h-4 w-4" /> Transit Access
              </h4>
              <div className="flex flex-wrap gap-2">
                {barrier.transit_matches.map((t) => (
                  <Badge key={t.route_number} variant="secondary" className="text-xs">
                    Route {t.route_number} — {t.route_name}
                  </Badge>
                ))}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
