"use client";

import { useQuery } from "@tanstack/react-query";
import { BarChart3, Users, Shield } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getDashboardStats } from "@/lib/api";

function humanize(id: string): string {
  return id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function CaseManagerPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: getDashboardStats,
  });

  return (
    <main className="min-h-screen px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold text-primary">Case Manager Dashboard</h1>
          <p className="text-muted-foreground">
            Aggregate metrics from MontGoWork assessments
          </p>
        </div>

        {isLoading && <p className="text-muted-foreground">Loading stats...</p>}
        {error && <p className="text-destructive">Failed to load dashboard data.</p>}

        {data && (
          <div className="grid gap-4 sm:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <Users className="h-4 w-4" /> Total Assessments
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-primary">{data.total_assessments}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <Shield className="h-4 w-4" /> Barrier Instances
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-primary">{data.total_barrier_instances}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" /> Avg Barriers/Person
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-primary">
                  {data.total_assessments > 0
                    ? (data.total_barrier_instances / data.total_assessments).toFixed(1)
                    : "0"}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {data && data.common_barriers.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Most Common Barriers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {data.common_barriers.map((item) => {
                  const pct = data.total_assessments > 0
                    ? Math.round((item.count / data.total_assessments) * 100)
                    : 0;
                  return (
                    <div key={item.barrier} className="flex items-center gap-3">
                      <span className="text-sm font-medium w-32">{humanize(item.barrier)}</span>
                      <div className="flex-1 h-4 rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full rounded-full bg-secondary transition-all"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground w-12 text-right">
                        {item.count} ({pct}%)
                      </span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </main>
  );
}
