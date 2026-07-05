import { useAdminOverview } from "@/lib/admin";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AdminOverview, SignupsPoint, WizardFunnel } from "@/types/admin";

export function AdminOverviewPage() {
  const { data, isLoading, isError } = useAdminOverview();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Overview</h1>
        <p className="text-sm text-muted-foreground">
          Snapshot of who's using the app and how far they're getting.
        </p>
      </div>

      {isLoading && <div className="text-sm text-muted-foreground">Loading…</div>}
      {isError && (
        <div className="text-sm text-destructive">
          Could not load overview. Check backend logs.
        </div>
      )}
      {data && (
        <>
          <TopStats overview={data} />
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Sign-ups (last 30 days)</CardTitle>
              </CardHeader>
              <CardContent>
                <SignupsChart series={data.signups_series} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Wizard funnel</CardTitle>
              </CardHeader>
              <CardContent>
                <FunnelBars funnel={data.funnel} />
              </CardContent>
            </Card>
          </div>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Entries by kind</CardTitle>
              </CardHeader>
              <CardContent>
                {data.entries_by_kind.length === 0 ? (
                  <div className="text-sm text-muted-foreground">
                    No entries created yet.
                  </div>
                ) : (
                  <table className="w-full text-sm">
                    <tbody>
                      {data.entries_by_kind.map((r) => (
                        <tr key={r.kind} className="border-b last:border-none">
                          <td className="py-2 capitalize">{r.kind}</td>
                          <td className="py-2 text-right tabular-nums">
                            {r.count.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Usage in last 7 days</CardTitle>
              </CardHeader>
              <CardContent>
                {data.usage_by_kind_7d.length === 0 ? (
                  <div className="text-sm text-muted-foreground">
                    No usage events yet.
                  </div>
                ) : (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-xs text-muted-foreground">
                        <th className="py-1 text-left font-normal">Kind</th>
                        <th className="py-1 text-right font-normal">Total</th>
                        <th className="py-1 text-right font-normal">Errors</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.usage_by_kind_7d.map((r) => (
                        <tr key={r.kind} className="border-b last:border-none">
                          <td className="py-2 font-mono text-xs">{r.kind}</td>
                          <td className="py-2 text-right tabular-nums">
                            {r.count.toLocaleString()}
                          </td>
                          <td className="py-2 text-right tabular-nums text-destructive">
                            {r.errors > 0 ? r.errors.toLocaleString() : ""}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function TopStats({ overview }: { overview: AdminOverview }) {
  const cells: [string, number, string?][] = [
    ["Users", overview.users_total, "total"],
    ["Students", overview.users_students],
    ["Active last 7d", overview.users_active_7d],
    ["Signups today", overview.signups_today],
    ["Signups last 7d", overview.signups_7d],
    ["Signups last 30d", overview.signups_30d],
  ];
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
      {cells.map(([label, value, sub]) => (
        <div key={label} className="rounded-md border bg-card p-3">
          <div className="text-xs text-muted-foreground">{label}</div>
          <div className="mt-1 text-2xl font-semibold tabular-nums">
            {value.toLocaleString()}
          </div>
          {sub && <div className="text-[10px] text-muted-foreground">{sub}</div>}
        </div>
      ))}
    </div>
  );
}

function SignupsChart({ series }: { series: SignupsPoint[] }) {
  const max = Math.max(1, ...series.map((s) => s.count));
  const W = 640;
  const H = 160;
  const P = 20;
  const step = (W - 2 * P) / Math.max(1, series.length - 1);
  const points = series
    .map((s, i) => {
      const x = P + i * step;
      const y = H - P - (s.count / max) * (H - 2 * P);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  const gridY = [0, 0.25, 0.5, 0.75, 1].map((f) => P + f * (H - 2 * P));
  return (
    <div className="w-full overflow-x-auto">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="none"
        className="w-full"
        style={{ height: H }}
      >
        {gridY.map((y, i) => (
          <line
            key={i}
            x1={P}
            y1={y}
            x2={W - P}
            y2={y}
            stroke="currentColor"
            strokeOpacity={0.08}
            strokeWidth={1}
          />
        ))}
        <polyline
          points={points}
          fill="none"
          stroke="currentColor"
          strokeOpacity={0.9}
          strokeWidth={2}
          className="text-primary"
        />
        {series.map((s, i) => {
          const x = P + i * step;
          const y = H - P - (s.count / max) * (H - 2 * P);
          return (
            <circle
              key={i}
              cx={x}
              cy={y}
              r={2.5}
              className="fill-primary"
            >
              <title>{`${s.day}: ${s.count}`}</title>
            </circle>
          );
        })}
      </svg>
      <div className="mt-1 flex justify-between text-[10px] text-muted-foreground">
        <span>{series[0]?.day}</span>
        <span>peak {max}</span>
        <span>{series[series.length - 1]?.day}</span>
      </div>
    </div>
  );
}

function FunnelBars({ funnel }: { funnel: WizardFunnel }) {
  const steps: [string, number][] = [
    ["Registered", funnel.registered],
    ["Basics", funnel.basics],
    ["Education", funnel.education],
    ["Photo", funnel.photo],
    ["Skills", funnel.skills],
    ["Courses", funnel.courses],
    ["Projects", funnel.projects],
    ["Volunteer", funnel.volunteer],
    ["Languages", funnel.languages],
    ["Certificates", funnel.certificates],
    ["Summary", funnel.summary],
    ["Preview", funnel.preview],
    ["Downloaded PDF", funnel.downloaded],
    ["Starter Pack", funnel.starter_pack],
  ];
  const max = Math.max(1, ...steps.map(([, c]) => c));
  return (
    <div className="space-y-1.5">
      {steps.map(([label, count], i) => {
        const pct = (count / max) * 100;
        const dropoff =
          i > 0 && steps[i - 1][1] > 0
            ? Math.round(100 - (count / steps[i - 1][1]) * 100)
            : null;
        return (
          <div key={label} className="grid grid-cols-[130px_1fr_60px] items-center gap-2">
            <div className="text-xs text-muted-foreground">{label}</div>
            <div className="relative h-4 rounded bg-muted">
              <div
                className="absolute inset-y-0 left-0 rounded bg-primary/80"
                style={{ width: `${pct}%` }}
              />
            </div>
            <div className="text-right text-xs tabular-nums">
              {count.toLocaleString()}
              {dropoff !== null && dropoff > 0 && (
                <span className="ml-1 text-[10px] text-destructive">
                  -{dropoff}%
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
