import { Activity, TrendingUp } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { useAnalyticsDashboard } from "@/lib/analytics";
import type {
  AnalyticsDashboardResponse,
  BucketMetrics,
  BudgetPerformance,
  DomainPerformance,
  RecentActivityEntry,
  TechnologyPerformance,
  TimeToStatusBucket,
} from "@/types/api";

const BUDGET_LABELS: Record<string, string> = {
  unknown: "Unknown",
  under_250: "Under $250",
  "250_500": "$250–500",
  "500_1000": "$500–1k",
  "1000_3000": "$1k–3k",
  "3000_plus": "$3k+",
};

const TIME_LABELS: Record<string, string> = {
  applied_to_viewed: "Applied → Viewed",
  applied_to_interview: "Applied → Interview",
  interview_to_offer: "Interview → Offer",
  offer_to_won: "Offer → Won",
  won_to_completed: "Won → Completed",
};

function pct(value: number | null | undefined, digits = 0): string {
  if (value == null) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

function money(value: string | null | undefined): string {
  if (value == null) return "—";
  return `$${Number(value).toLocaleString()}`;
}

function num(value: number | null | undefined, digits = 1): string {
  if (value == null) return "—";
  return value.toFixed(digits);
}

function hours(value: number | null | undefined): string {
  if (value == null) return "—";
  if (value < 48) return `${value.toFixed(1)}h`;
  return `${(value / 24).toFixed(1)}d`;
}

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-3xl tabular-nums">{value}</CardTitle>
      </CardHeader>
      {hint && <CardContent className="text-xs text-muted-foreground">{hint}</CardContent>}
    </Card>
  );
}

function EmptyHint({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-md border border-dashed border-border/70 p-4 text-sm text-muted-foreground">
      {children}
    </div>
  );
}

function OverviewSection({ data }: { data: AnalyticsDashboardResponse }) {
  const o = data.overview;
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      <Stat label="Applications" value={String(o.total_applications)} hint={`${o.active_applications} active`} />
      <Stat label="Interviews" value={String(o.interviewed_count)} />
      <Stat label="Wins" value={String(o.won_count)} hint={`${o.completed_count} completed · ${o.lost_count} lost`} />
      <Stat label="Revenue" value={money(o.total_revenue)} hint={`avg contract ${money(o.average_contract_amount)}`} />
      <Stat label="Avg opportunity score" value={num(o.average_opportunity_score)} />
      <Stat label="Avg proposal quality" value={num(o.average_proposal_quality_score)} />
    </div>
  );
}

function FunnelSection({ data }: { data: AnalyticsDashboardResponse }) {
  const f = data.funnel;
  const o = data.outcomes;
  const stages = [
    { label: "Applied", count: f.applied, rate: 1.0 },
    { label: "Viewed", count: f.viewed, rate: o.viewed_rate },
    { label: "Interview", count: f.interview, rate: o.interview_rate },
    { label: "Offer", count: f.offer, rate: o.offer_rate },
    { label: "Won", count: f.won, rate: o.win_rate },
    { label: "Completed", count: f.completed, rate: o.completion_rate },
  ];
  if (f.applied === 0) {
    return <EmptyHint>Apply to at least one job to see funnel rates.</EmptyHint>;
  }
  const max = Math.max(...stages.map((s) => s.count), 1);
  return (
    <div className="space-y-2">
      {stages.map((s) => (
        <div key={s.label} className="grid grid-cols-[8rem_1fr_5rem] items-center gap-3">
          <span className="text-sm text-muted-foreground">{s.label}</span>
          <div className="h-6 overflow-hidden rounded-md bg-muted">
            <div
              className="h-full rounded-md bg-primary/80"
              style={{ width: `${(s.count / max) * 100}%` }}
            />
          </div>
          <div className="text-right text-sm tabular-nums">
            <span className="font-medium">{s.count}</span>
            <span className="ml-1 text-xs text-muted-foreground">{pct(s.rate)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function BucketTable({
  buckets,
  showQuality = true,
}: {
  buckets: BucketMetrics[];
  showQuality?: boolean;
}) {
  if (buckets.every((b) => b.applications === 0)) {
    return <EmptyHint>Not enough data yet.</EmptyHint>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-xs uppercase tracking-wider text-muted-foreground">
            <th className="py-2 pr-3">Bucket</th>
            <th className="py-2 pr-3 text-right">Apps</th>
            <th className="py-2 pr-3 text-right">Interview rate</th>
            <th className="py-2 pr-3 text-right">Win rate</th>
            {showQuality && <th className="py-2 pr-3 text-right">Avg quality</th>}
            <th className="py-2 pr-3 text-right">Avg contract</th>
          </tr>
        </thead>
        <tbody>
          {buckets.map((b) => (
            <tr key={b.label} className="border-b border-border/40">
              <td className="py-2 pr-3 font-medium">{b.label}</td>
              <td className="py-2 pr-3 text-right tabular-nums">{b.applications}</td>
              <td className="py-2 pr-3 text-right tabular-nums">{pct(b.interview_rate)}</td>
              <td className="py-2 pr-3 text-right tabular-nums">{pct(b.win_rate)}</td>
              {showQuality && (
                <td className="py-2 pr-3 text-right tabular-nums">{num(b.average_quality_score)}</td>
              )}
              <td className="py-2 pr-3 text-right tabular-nums">{money(b.average_contract_amount)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TechnologySection({ items }: { items: TechnologyPerformance[] }) {
  if (!items.length) return <EmptyHint>No technologies detected yet.</EmptyHint>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-xs uppercase tracking-wider text-muted-foreground">
            <th className="py-2 pr-3">Technology</th>
            <th className="py-2 pr-3 text-right">Apps</th>
            <th className="py-2 pr-3 text-right">Interviews</th>
            <th className="py-2 pr-3 text-right">Wins</th>
            <th className="py-2 pr-3 text-right">Win rate</th>
            <th className="py-2 pr-3 text-right">Avg score</th>
          </tr>
        </thead>
        <tbody>
          {items.map((t) => (
            <tr key={t.technology} className="border-b border-border/40">
              <td className="py-2 pr-3 font-medium">{t.technology}</td>
              <td className="py-2 pr-3 text-right tabular-nums">{t.applications}</td>
              <td className="py-2 pr-3 text-right tabular-nums">{t.interviews}</td>
              <td className="py-2 pr-3 text-right tabular-nums">{t.wins}</td>
              <td className="py-2 pr-3 text-right tabular-nums">{pct(t.win_rate)}</td>
              <td className="py-2 pr-3 text-right tabular-nums">{num(t.average_opportunity_score)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DomainSection({ items }: { items: DomainPerformance[] }) {
  if (!items.length) return <EmptyHint>No domains detected yet.</EmptyHint>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-xs uppercase tracking-wider text-muted-foreground">
            <th className="py-2 pr-3">Domain</th>
            <th className="py-2 pr-3 text-right">Apps</th>
            <th className="py-2 pr-3 text-right">Interviews</th>
            <th className="py-2 pr-3 text-right">Wins</th>
            <th className="py-2 pr-3 text-right">Win rate</th>
            <th className="py-2 pr-3 text-right">Avg contract</th>
          </tr>
        </thead>
        <tbody>
          {items.map((d) => (
            <tr key={d.domain} className="border-b border-border/40">
              <td className="py-2 pr-3 font-medium">{d.domain}</td>
              <td className="py-2 pr-3 text-right tabular-nums">{d.applications}</td>
              <td className="py-2 pr-3 text-right tabular-nums">{d.interviews}</td>
              <td className="py-2 pr-3 text-right tabular-nums">{d.wins}</td>
              <td className="py-2 pr-3 text-right tabular-nums">{pct(d.win_rate)}</td>
              <td className="py-2 pr-3 text-right tabular-nums">{money(d.average_contract_amount)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function BudgetSection({ items }: { items: BudgetPerformance[] }) {
  const chartData = items.map((b) => ({
    bucket: BUDGET_LABELS[b.bucket] ?? b.bucket,
    apps: b.applications,
    wins: b.wins,
  }));
  if (items.every((b) => b.applications === 0)) {
    return <EmptyHint>No applications with budget data yet.</EmptyHint>;
  }
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer>
        <BarChart data={chartData} margin={{ left: 0, right: 10, top: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            dataKey="bucket"
            stroke="hsl(var(--muted-foreground))"
            tick={{ fontSize: 11 }}
          />
          <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 11 }} allowDecimals={false} />
          <Tooltip
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              fontSize: 12,
            }}
          />
          <Bar dataKey="apps" fill="hsl(var(--primary))" />
          <Bar dataKey="wins" fill="#10b981" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function RevenueSection({ data }: { data: AnalyticsDashboardResponse }) {
  const r = data.revenue;
  const points = r.revenue_by_month.map((m) => ({
    month: m.month,
    revenue: Number(m.revenue),
    wins: m.wins,
  }));
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-3">
        <Stat label="Total" value={money(r.total_revenue)} />
        <Stat label="Completed" value={money(r.completed_revenue)} hint="Status = completed" />
        <Stat label="Projected" value={money(r.projected_revenue)} hint="Won but not completed" />
      </div>
      {points.length === 0 ? (
        <EmptyHint>No revenue recorded yet — add a contract amount to a won application.</EmptyHint>
      ) : (
        <div className="h-56 w-full">
          <ResponsiveContainer>
            <LineChart data={points} margin={{ left: 0, right: 10, top: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 11 }} />
              <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  fontSize: 12,
                }}
                formatter={(value: number) => `$${value.toLocaleString()}`}
              />
              <Line
                type="monotone"
                dataKey="revenue"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                dot={{ r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function TimeToStatusSection({ buckets }: { buckets: TimeToStatusBucket[] }) {
  const hasData = buckets.some((b) => b.count > 0);
  if (!hasData) {
    return <EmptyHint>No status transitions recorded yet.</EmptyHint>;
  }
  return (
    <div className="space-y-2">
      {buckets.map((b) => (
        <div
          key={b.label}
          className="grid grid-cols-[10rem_1fr_4rem_4rem] items-center gap-3 text-sm"
        >
          <span className="text-muted-foreground">{TIME_LABELS[b.label] ?? b.label}</span>
          <div className="text-xs text-muted-foreground">
            {b.count === 0 ? "—" : `${b.count} sample${b.count === 1 ? "" : "s"}`}
          </div>
          <div className="text-right tabular-nums">{hours(b.avg_hours)}</div>
          <div className="text-right tabular-nums text-muted-foreground">{hours(b.p90_hours)}</div>
        </div>
      ))}
      <div className="grid grid-cols-[10rem_1fr_4rem_4rem] gap-3 pt-1 text-[10px] uppercase tracking-wider text-muted-foreground">
        <span />
        <span />
        <span className="text-right">avg</span>
        <span className="text-right">p90</span>
      </div>
    </div>
  );
}

const STATUS_BADGE_STYLE: Record<string, string> = {
  applied: "bg-blue-500/15 text-blue-400",
  viewed: "bg-blue-500/15 text-blue-300",
  interview: "bg-violet-500/15 text-violet-300",
  offer: "bg-amber-500/15 text-amber-400",
  won: "bg-emerald-500/15 text-emerald-400",
  completed: "bg-emerald-500/15 text-emerald-300",
  rejected: "bg-rose-500/15 text-rose-400",
  withdrawn: "bg-zinc-500/15 text-zinc-300",
  draft: "bg-muted text-muted-foreground",
};

function RecentActivitySection({ items }: { items: RecentActivityEntry[] }) {
  if (!items.length) return <EmptyHint>No status changes yet.</EmptyHint>;
  return (
    <ul className="space-y-2">
      {items.map((h, i) => (
        <li
          key={`${h.application_id}-${i}`}
          className="rounded-md border border-border/70 px-3 py-2 text-sm"
        >
          <div className="flex items-baseline justify-between gap-3">
            <Link
              to={`/applications/${h.application_id}`}
              className="truncate font-medium hover:underline"
            >
              {h.job_title ?? "Application"}
            </Link>
            <span className="shrink-0 text-xs text-muted-foreground">
              {new Date(h.created_at).toLocaleString()}
            </span>
          </div>
          <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
            <span>{h.from_status ?? "(initial)"} →</span>
            <span
              className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                STATUS_BADGE_STYLE[h.to_status] ?? "bg-muted text-muted-foreground"
              }`}
            >
              {h.to_status}
            </span>
            {h.note && <span className="italic">{h.note}</span>}
          </div>
        </li>
      ))}
    </ul>
  );
}

export function AnalyticsPage() {
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const { data, isLoading } = useAnalyticsDashboard({
    from_date: fromDate || undefined,
    to_date: toDate || undefined,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Analytics</h1>
          <p className="text-sm text-muted-foreground">
            Outcomes computed from immutable application snapshots and history.
          </p>
        </div>
        <div className="flex items-end gap-2">
          <div className="space-y-1">
            <Label htmlFor="from" className="text-xs">From</Label>
            <Input
              id="from"
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="w-36"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="to" className="text-xs">To</Label>
            <Input
              id="to"
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="w-36"
            />
          </div>
          {(fromDate || toDate) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setFromDate("");
                setToDate("");
              }}
            >
              Reset
            </Button>
          )}
        </div>
      </div>

      {isLoading ? (
        <div className="text-sm text-muted-foreground">Loading…</div>
      ) : !data ? (
        <EmptyHint>Could not load analytics.</EmptyHint>
      ) : data.overview.total_applications === 0 ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            No applications in this date range yet. Generate a proposal and click{" "}
            <span className="font-medium text-foreground">Mark as Applied</span> on any job — or
            run <code className="rounded bg-muted px-1.5 py-0.5">make seed</code> for a richer
            demo dataset.
          </CardContent>
        </Card>
      ) : (
        <>
          <OverviewSection data={data} />

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Funnel</CardTitle>
                <CardDescription>
                  Counts use timestamps, so a current win still contributes to viewed/interview/offer.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <FunnelSection data={data} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Activity className="h-4 w-4 text-primary" /> Time to status
                </CardTitle>
                <CardDescription>How long does each step actually take?</CardDescription>
              </CardHeader>
              <CardContent>
                <TimeToStatusSection buckets={data.time_to_status.buckets} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Opportunity score effectiveness</CardTitle>
                <CardDescription>Does a higher score actually win more?</CardDescription>
              </CardHeader>
              <CardContent>
                <BucketTable buckets={data.score_effectiveness.buckets} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Proposal quality effectiveness</CardTitle>
                <CardDescription>And does a higher quality proposal?</CardDescription>
              </CardHeader>
              <CardContent>
                <BucketTable buckets={data.proposal_quality_effectiveness.buckets} showQuality={false} />
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Technology performance</CardTitle>
              <CardDescription>Extracted from each application's snapshot.</CardDescription>
            </CardHeader>
            <CardContent>
              <TechnologySection items={data.technologies} />
            </CardContent>
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Domain performance</CardTitle>
              </CardHeader>
              <CardContent>
                <DomainSection items={data.domains} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Budget performance</CardTitle>
                <CardDescription>
                  Bars: <span className="font-medium text-foreground">apps</span>
                  {" · "}
                  <span className="font-medium text-foreground">wins</span>
                </CardDescription>
              </CardHeader>
              <CardContent>
                <BudgetSection items={data.budgets} />
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <TrendingUp className="h-4 w-4 text-primary" /> Revenue
              </CardTitle>
              <CardDescription>
                From won + completed applications with a contract amount.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <RevenueSection data={data} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recent activity</CardTitle>
              <CardDescription>Last 10 status changes.</CardDescription>
            </CardHeader>
            <CardContent>
              <RecentActivitySection items={data.recent_activity.items} />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

