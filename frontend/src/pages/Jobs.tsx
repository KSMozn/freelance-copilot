import { useQuery } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, ArrowUpDown, ImageDown, Plus, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { api } from "@/app/apiClient";
import {
  SCORE_DIMENSION_LABELS,
  SCORE_DIMENSION_MAX,
  type Job,
  type JobListResponse,
  type JobSortBy,
  type JobStatus,
  type ScoreBreakdown,
  type SortDir,
} from "@/types/api";

const STATUSES: { value: JobStatus | ""; label: string }[] = [
  { value: "", label: "All" },
  { value: "new", label: "New" },
  { value: "shortlisted", label: "Shortlisted" },
  { value: "applied", label: "Applied" },
  { value: "ignored", label: "Ignored" },
  { value: "archived", label: "Archived" },
];

type BreakdownDim = keyof ScoreBreakdown;

const BREAKDOWN_COLUMNS: { dim: BreakdownDim; short: string; sortKey: JobSortBy }[] = [
  { dim: "technical_fit", short: "Tech", sortKey: "score.technical_fit" },
  { dim: "domain_fit", short: "Domain", sortKey: "score.domain_fit" },
  { dim: "proposal_count", short: "Prop", sortKey: "score.proposal_count" },
  { dim: "budget_attractiveness", short: "Budget", sortKey: "score.budget_attractiveness" },
  { dim: "client_quality", short: "Client", sortKey: "score.client_quality" },
  { dim: "estimated_effort", short: "Effort", sortKey: "score.estimated_effort" },
  { dim: "risk_level", short: "Risk", sortKey: "score.risk_level" },
  { dim: "strategic_value", short: "Strat", sortKey: "score.strategic_value" },
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

function totalScoreTone(score: number): string {
  if (score >= 80) return "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300";
  if (score >= 65) return "bg-sky-500/15 text-sky-700 dark:text-sky-300";
  if (score >= 50) return "bg-amber-500/15 text-amber-700 dark:text-amber-300";
  return "bg-rose-500/15 text-rose-700 dark:text-rose-300";
}

function ScoreChip({ score }: { score: number | null | undefined }) {
  if (score == null) return <span className="text-xs text-muted-foreground">—</span>;
  return (
    <span
      className={`inline-flex items-center rounded-md px-1.5 py-0.5 text-xs font-medium tabular-nums ${totalScoreTone(
        score,
      )}`}
      title="Opportunity score (0–100)"
    >
      {score}
    </span>
  );
}

function BreakdownCell({ value, max }: { value: number | undefined; max: number }) {
  if (value == null) return <span className="text-xs text-muted-foreground">—</span>;
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div className="flex flex-col items-end gap-0.5">
      <span className="text-xs tabular-nums">
        <span className="font-medium">{value}</span>
        <span className="text-muted-foreground">/{max}</span>
      </span>
      <div className="h-1 w-12 overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function SortHeader({
  label,
  align = "left",
  sortKey,
  current,
  dir,
  onSort,
  title,
}: {
  label: string;
  align?: "left" | "right";
  sortKey?: JobSortBy;
  current: JobSortBy;
  dir: SortDir;
  onSort: (key: JobSortBy) => void;
  title?: string;
}) {
  const sortable = !!sortKey;
  const active = sortable && current === sortKey;
  const Icon = !active ? ArrowUpDown : dir === "asc" ? ArrowUp : ArrowDown;
  const justify = align === "right" ? "justify-end" : "justify-start";
  return (
    <th
      className={`px-2 py-2 text-${align} text-xs font-medium text-muted-foreground ${
        sortable ? "cursor-pointer select-none hover:text-foreground" : ""
      }`}
      onClick={sortable ? () => onSort(sortKey!) : undefined}
      title={title ?? (sortable ? `Sort by ${label}` : undefined)}
    >
      <span className={`inline-flex items-center gap-1 ${justify}`}>
        {label}
        {sortable && (
          <Icon className={`h-3 w-3 ${active ? "text-foreground" : "opacity-50"}`} />
        )}
      </span>
    </th>
  );
}

export function JobsPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<JobStatus | "">("");
  const [sortBy, setSortBy] = useState<JobSortBy>("created_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const params = useMemo(() => {
    const p: Record<string, string | number> = {
      limit: 50,
      sort_by: sortBy,
      sort_dir: sortDir,
    };
    if (search.trim()) p.search = search.trim();
    if (status) p.status = status;
    return p;
  }, [search, status, sortBy, sortDir]);

  const { data, isLoading } = useQuery({
    queryKey: ["jobs", params],
    queryFn: async () => {
      const { data } = await api.get<JobListResponse>("/jobs", { params });
      return data;
    },
  });

  const onSort = (key: JobSortBy) => {
    if (sortBy === key) {
      setSortDir((d) => (d === "desc" ? "asc" : "desc"));
    } else {
      setSortBy(key);
      // Score columns default to high-to-low; title defaults to A→Z.
      setSortDir(key === "title" ? "asc" : "desc");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Jobs</h1>
          <p className="text-sm text-muted-foreground">
            Paste a job, or upload an Upwork screenshot. Nothing is scraped.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link to="/jobs/import">
              <ImageDown className="mr-2 h-4 w-4" />
              Import from screenshot
            </Link>
          </Button>
          <Button asChild>
            <Link to="/jobs/new">
              <Plus className="mr-2 h-4 w-4" />
              Paste job
            </Link>
          </Button>
        </div>
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
            <div className="overflow-x-auto">
              <table className="w-full min-w-[1000px] text-sm">
                <thead className="border-b bg-muted/30">
                  <tr>
                    <SortHeader
                      label="Job"
                      sortKey="title"
                      current={sortBy}
                      dir={sortDir}
                      onSort={onSort}
                    />
                    {BREAKDOWN_COLUMNS.map((c) => (
                      <SortHeader
                        key={c.dim}
                        label={c.short}
                        align="right"
                        sortKey={c.sortKey}
                        current={sortBy}
                        dir={sortDir}
                        onSort={onSort}
                        title={`Sort by ${SCORE_DIMENSION_LABELS[c.dim]} (out of ${SCORE_DIMENSION_MAX[c.dim]})`}
                      />
                    ))}
                    <SortHeader
                      label="Total"
                      align="right"
                      sortKey="score"
                      current={sortBy}
                      dir={sortDir}
                      onSort={onSort}
                      title="Sort by total opportunity score (out of 100)"
                    />
                    <SortHeader label="Status" align="right" current={sortBy} dir={sortDir} onSort={onSort} />
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((j: Job) => {
                    const total = j.opportunity_score?.score ?? null;
                    const breakdown = j.opportunity_score?.score_breakdown;
                    return (
                      <tr key={j.id} className="border-b last:border-b-0 hover:bg-accent/40">
                        <td className="px-2 py-3">
                          <Link to={`/jobs/${j.id}`} className="block">
                            <div className="flex items-center gap-2">
                              <span className="truncate font-medium">{j.title}</span>
                              <ScoreChip score={total} />
                            </div>
                            <div className="truncate text-xs text-muted-foreground">
                              {j.budget_type ?? "—"} · {j.currency} {j.budget_min ?? "?"}–{j.budget_max ?? "?"} ·{" "}
                              {j.proposal_count ?? "?"} proposals
                            </div>
                          </Link>
                        </td>
                        {BREAKDOWN_COLUMNS.map((c) => (
                          <td key={c.dim} className="px-2 py-3 text-right align-middle">
                            <BreakdownCell value={breakdown?.[c.dim]} max={SCORE_DIMENSION_MAX[c.dim]} />
                          </td>
                        ))}
                        <td className="px-2 py-3 text-right align-middle">
                          {total != null ? (
                            <span className="text-sm font-semibold tabular-nums">{total}</span>
                          ) : (
                            <span className="text-xs text-muted-foreground">—</span>
                          )}
                          {total != null && <span className="text-xs text-muted-foreground">/100</span>}
                        </td>
                        <td className="px-2 py-3 text-right align-middle">
                          <StatusBadge status={j.status} />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
