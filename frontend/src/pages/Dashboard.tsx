import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { api } from "@/app/apiClient";
import type { JobListResponse } from "@/types/api";

function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-3xl">{value}</CardTitle>
      </CardHeader>
      {hint && <CardContent className="text-xs text-muted-foreground">{hint}</CardContent>}
    </Card>
  );
}

export function DashboardPage() {
  const { data } = useQuery({
    queryKey: ["jobs", { limit: 5 }],
    queryFn: async () => {
      const { data } = await api.get<JobListResponse>("/jobs", { params: { limit: 5 } });
      return data;
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Phase 1 — foundation only. Scoring, analysis, and proposals arrive in later phases.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <StatCard label="Imported jobs" value={String(data?.total ?? 0)} hint="Manually pasted" />
        <StatCard label="Applications" value="—" hint="Phase 7" />
        <StatCard label="Win rate" value="—" hint="Phase 8" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent jobs</CardTitle>
          <CardDescription>The five most recently imported jobs.</CardDescription>
        </CardHeader>
        <CardContent>
          {!data?.items.length ? (
            <div className="text-sm text-muted-foreground">No jobs yet. Import one to get started.</div>
          ) : (
            <ul className="divide-y">
              {data.items.map((j) => (
                <li key={j.id} className="flex items-center justify-between py-2 text-sm">
                  <span className="truncate">{j.title}</span>
                  <span className="text-muted-foreground">{j.status}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
