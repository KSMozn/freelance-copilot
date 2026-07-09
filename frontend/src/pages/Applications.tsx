import { Briefcase, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { useApplicationList } from "@/lib/applications";
import { cn } from "@/shared/lib/utils";
import {
  APPLICATION_STATUS_ORDER,
  type Application,
  type ApplicationStatus,
} from "@/types/api";

const STATUS_LABEL: Record<ApplicationStatus, string> = {
  draft: "Draft",
  applied: "Applied",
  viewed: "Viewed",
  interview: "Interview",
  offer: "Offer",
  won: "Won",
  completed: "Completed",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
};

const STATUS_BADGE_STYLE: Record<ApplicationStatus, string> = {
  draft: "bg-muted text-muted-foreground",
  applied: "bg-blue-500/15 text-blue-400",
  viewed: "bg-blue-500/15 text-blue-300",
  interview: "bg-violet-500/15 text-violet-300",
  offer: "bg-amber-500/15 text-amber-400",
  won: "bg-emerald-500/15 text-emerald-400",
  completed: "bg-emerald-500/15 text-emerald-300",
  rejected: "bg-rose-500/15 text-rose-400",
  withdrawn: "bg-zinc-500/15 text-zinc-300",
};

function formatDate(value: string | null): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleDateString();
  } catch {
    return value;
  }
}

function ApplicationCard({ app }: { app: Application }) {
  const snapshot = app.snapshot;
  const title = snapshot?.job?.title ?? "Untitled job";
  const oppScore = snapshot?.opportunity_score?.score;
  const qualityScore = snapshot?.proposal?.quality_score;
  return (
    <Link
      to={`/applications/${app.id}`}
      className="block rounded-md border border-border/70 bg-card p-3 transition-colors hover:border-primary/40"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="truncate text-sm font-medium">{title}</div>
          <div className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
            <Briefcase className="h-3 w-3" />
            <span>{formatDate(app.applied_at ?? app.created_at)}</span>
            {app.contract_amount && <span>· ${app.contract_amount}</span>}
          </div>
        </div>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-1.5 text-[11px]">
        {oppScore != null && <Badge variant="outline">Score {oppScore}</Badge>}
        {qualityScore != null && (
          <Badge variant="outline">Quality {qualityScore}</Badge>
        )}
      </div>
    </Link>
  );
}

function StatusColumn({
  status,
  apps,
}: {
  status: ApplicationStatus;
  apps: Application[];
}) {
  return (
    <div className="flex w-72 shrink-0 flex-col rounded-md border border-border/70 bg-card/40">
      <div className="flex items-center justify-between px-3 py-2">
        <span className={cn("rounded px-2 py-0.5 text-xs font-semibold", STATUS_BADGE_STYLE[status])}>
          {STATUS_LABEL[status]}
        </span>
        <span className="text-xs text-muted-foreground tabular-nums">{apps.length}</span>
      </div>
      <div className="space-y-2 p-2">
        {apps.length === 0 ? (
          <div className="px-2 py-4 text-center text-xs text-muted-foreground">—</div>
        ) : (
          apps.map((a) => <ApplicationCard key={a.id} app={a} />)
        )}
      </div>
    </div>
  );
}

export function ApplicationsPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<ApplicationStatus | "">("");

  const { data, isLoading } = useApplicationList({
    status: statusFilter || undefined,
    search,
  });

  const grouped = useMemo(() => {
    const groups: Record<ApplicationStatus, Application[]> = {
      draft: [],
      applied: [],
      viewed: [],
      interview: [],
      offer: [],
      won: [],
      completed: [],
      rejected: [],
      withdrawn: [],
    };
    for (const app of data?.items ?? []) {
      groups[app.status]?.push(app);
    }
    return groups;
  }, [data?.items]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Applications</h1>
          <p className="text-sm text-muted-foreground">
            Track applications from drafted to completed. Snapshots preserve the
            exact proposal, resume, and portfolio context used at submission.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search job title…"
            className="pl-9"
          />
        </div>
        <div className="flex flex-wrap gap-1">
          <Button
            size="sm"
            variant={statusFilter === "" ? "default" : "outline"}
            onClick={() => setStatusFilter("")}
          >
            All
          </Button>
          {APPLICATION_STATUS_ORDER.map((s) => (
            <Button
              key={s}
              size="sm"
              variant={statusFilter === s ? "default" : "outline"}
              onClick={() => setStatusFilter(s)}
            >
              {STATUS_LABEL[s]}
            </Button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="text-sm text-muted-foreground">Loading…</div>
      ) : !data?.items.length ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            No applications yet. Generate a proposal on a job and click
            <span className="font-medium text-foreground"> Mark as Applied</span> to
            create one.
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto pb-2">
          <div className="flex gap-3">
            {APPLICATION_STATUS_ORDER.map((s) => (
              <StatusColumn key={s} status={s} apps={grouped[s] ?? []} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
