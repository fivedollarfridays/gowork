"use client";

import { useState, useCallback } from "react";
import { Zap, TrendingUp, Briefcase, Gift, Loader2, RotateCcw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export interface SimulationResults {
  barriers_resolved: string[];
  barriers_remaining: string[];
  unlocked_barriers: string[];
  jobs_unlocked_estimate: number;
  benefits_unlocked: string[];
  sequence_after: {
    steps: unknown[];
    total_barriers: number;
    has_cycles: boolean;
  };
}

interface Props {
  barriers: string[];
  onSimulate: (resolved: string[]) => void;
  simulationResults?: SimulationResults;
  isLoading?: boolean;
}

function humanizeBarrier(id: string): string {
  return id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function SummarySentence({ results }: { results: SimulationResults }) {
  const count = results.barriers_resolved.length;
  if (count === 0) return null;

  return (
    <p className="text-sm font-medium text-foreground mt-3" role="status">
      Resolving these {count} barrier{count > 1 ? "s" : ""} unlocks{" "}
      <strong>+{results.jobs_unlocked_estimate}</strong> more jobs
      {results.benefits_unlocked.length > 0 && (
        <> and <strong>{results.benefits_unlocked.length}</strong> benefits</>
      )}
      .
    </p>
  );
}

function ImpactSummary({ results }: { results: SimulationResults }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 mt-4">
      <div className="flex items-center gap-2 rounded-lg border p-3">
        <Briefcase className="h-5 w-5 text-secondary shrink-0" />
        <div>
          <div className="text-lg font-bold text-secondary">
            +{results.jobs_unlocked_estimate}
          </div>
          <div className="text-xs text-muted-foreground">Additional jobs accessible</div>
        </div>
      </div>

      {results.benefits_unlocked.length > 0 && (
        <div className="flex items-start gap-2 rounded-lg border p-3">
          <Gift className="h-5 w-5 text-secondary shrink-0 mt-0.5" />
          <div>
            <div className="text-sm font-medium">Benefits unlocked</div>
            <ul className="text-xs text-muted-foreground space-y-0.5 mt-1">
              {results.benefits_unlocked.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {results.unlocked_barriers.length > 0 && (
        <div className="flex items-start gap-2 rounded-lg border p-3 sm:col-span-2">
          <TrendingUp className="h-5 w-5 text-secondary shrink-0 mt-0.5" />
          <div>
            <div className="text-sm font-medium">Cascading unlocks</div>
            <div className="flex flex-wrap gap-1 mt-1">
              {results.unlocked_barriers.map((b) => (
                <Badge key={b} variant="outline" className="text-xs">
                  {humanizeBarrier(b)}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      )}

      <SummarySentence results={results} />
    </div>
  );
}

export function WhatHappensIf({ barriers, onSimulate, simulationResults, isLoading }: Props) {
  const [resolved, setResolved] = useState<Set<string>>(new Set());

  const handleToggle = useCallback(
    (barrier: string) => {
      setResolved((prev) => {
        const next = new Set(prev);
        if (next.has(barrier)) {
          next.delete(barrier);
        } else {
          next.add(barrier);
        }
        onSimulate(Array.from(next));
        return next;
      });
    },
    [onSimulate],
  );

  const handleReset = useCallback(() => {
    setResolved(new Set());
    onSimulate([]);
  }, [onSimulate]);

  if (barriers.length === 0) {
    return (
      <Card>
        <CardContent className="py-6 text-center">
          <p className="text-sm text-muted-foreground">
            No barriers identified to simulate.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Zap className="h-5 w-5 text-secondary" />
            What Happens If...?
          </CardTitle>
          {resolved.size > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReset}
              aria-label="Reset all toggles"
            >
              <RotateCcw className="h-3.5 w-3.5 mr-1" />
              Reset
            </Button>
          )}
        </div>
        <p className="text-sm text-muted-foreground">
          Toggle barriers to see the cascading effect on your job matches and benefits
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {barriers.map((barrier) => (
            <label
              key={barrier}
              className="flex items-center justify-between rounded-lg border p-3 cursor-pointer hover:bg-muted/50 transition-colors"
            >
              <span className="text-sm font-medium">
                {humanizeBarrier(barrier)}
              </span>
              <button
                type="button"
                role="switch"
                aria-checked={resolved.has(barrier)}
                aria-label={`Resolve ${humanizeBarrier(barrier)}`}
                onClick={() => handleToggle(barrier)}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                  resolved.has(barrier) ? "bg-secondary" : "bg-input"
                }`}
              >
                <span
                  className={`pointer-events-none block h-5 w-5 rounded-full bg-background shadow-lg ring-0 transition-transform ${
                    resolved.has(barrier) ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </label>
          ))}
        </div>

        {isLoading && (
          <div className="flex items-center gap-2 mt-4 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Calculating impact...
          </div>
        )}

        {!isLoading && simulationResults && <ImpactSummary results={simulationResults} />}
      </CardContent>
    </Card>
  );
}
