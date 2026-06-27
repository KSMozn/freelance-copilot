import { useQuery } from "@tanstack/react-query";
import { Plus, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { Job, JobListResponse, JobStatus } from "@/types/api";

const STATUSES: { value: JobStatus | ""; label: string }[] = [
  { value: "", label: "All" },
  { value: "new", label: "New" },
  { value: "shortlisted", label: "Shortlisted" },
  { value: "applied", label: "Applied" },
  { value: "ignored", label: "Ignored" },
  { value: "archived", label: "Archived" },
];

function StatusBadge({ status }: { status: JobStatus }) {
  const variant =
    status === "applied"
      ? "default"
      : status === "shortlisted"
      ? "secondary"
      : status === "ignored" || status === "archived"
      ? "outline"
      : "secondary";
  return <Badge variant={variant}>{status}</Badge>;
}

export function JobsPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<JobStatus | "">("");

  const params = useMemo(() => {
    const p: Record<string, string | number> = { limit: 50 };
    if (search.trim()) p.search = search.trim();
    if (status) p.status = status;
    return p;
  }, [search, status]);

  const { data, isLoading } = useQuery({
    queryKey: ["jobs", params],
    queryFn: async () => {
      const { data } = await api.get<JobListResponse>("/jobs", { params });
      return data;
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Jobs</h1>
          <p className="text-sm text-muted-foreground">Paste a job to import it. Nothing is scraped.</p>
        </div>
        <Button asChild>
          <Link to="/jobs/new">
            <Plus className="mr-2 h-4 w-4" />
            Import job
          </Link>
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search jobs…"
            className="pl-9"
          />
        </div>
        <div className="flex gap-1">
          {STATUSES.map((s) => (
            <Button
              key={s.value || "all"}
              size="sm"
              variant={status === s.value ? "default" : "outline"}
              onClick={() => setStatus(s.value)}
            >
              {s.label}
            </Button>
          ))}
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 text-sm text-muted-foreground">Loading…</div>
          ) : !data?.items.length ? (
            <div className="p-6 text-sm text-muted-foreground">No jobs match.</div>
          ) : (
            <ul className="divide-y">
              {data.items.map((j: Job) => (
                <li key={j.id}>
                  <Link to={`/jobs/${j.id}`} className="flex items-center justify-between px-6 py-3 hover:bg-accent/40">
                    <div className="min-w-0">
                      <div className="truncate font-medium">{j.title}</div>
                      <div className="truncate text-xs text-muted-foreground">
                        {j.budget_type ?? "—"} · {j.currency} {j.budget_min ?? "?"}–{j.budget_max ?? "?"} ·{" "}
                        {j.proposal_count ?? "?"} proposals
                      </div>
                    </div>
                    <StatusBadge status={j.status} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
