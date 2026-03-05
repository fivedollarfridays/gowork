"use client";

import { Bus, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { TransitConnection } from "@/lib/types";

interface TransitInfoProps {
  routes: TransitConnection[];
}

export function TransitInfo({ routes }: TransitInfoProps) {
  if (routes.length === 0) return null;

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium flex items-center gap-1.5">
        <Bus className="h-4 w-4" /> Transit Routes
      </h4>
      <div className="space-y-2">
        {routes.map((route) => {
          const schedule = route.schedule.toLowerCase();
          const noSunday = schedule.includes("no sunday");
          const noLateNight = schedule.includes("no late") || schedule.includes("9pm") || schedule.includes("9:00");

          return (
            <div key={route.route_number} className="flex flex-wrap items-center gap-2 text-sm">
              <Badge variant="secondary" className="text-xs">
                Route {route.route_number}
              </Badge>
              <span className="text-muted-foreground">{route.route_name}</span>
              {noSunday && (
                <Badge variant="outline" className="text-xs text-destructive border-destructive/30 gap-1">
                  <AlertTriangle className="h-3 w-3" />
                  No Sunday
                </Badge>
              )}
              {noLateNight && (
                <Badge variant="outline" className="text-xs text-destructive border-destructive/30 gap-1">
                  <AlertTriangle className="h-3 w-3" />
                  No Late Night
                </Badge>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
