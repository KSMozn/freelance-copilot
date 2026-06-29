import { Gauge } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { InterviewChance, JobConfidenceReport } from "@/types/api";

function pctTone(value: number): string {
  if (value >= 80) return "text-emerald-400";
  if (value >= 60) return "text-sky-400";
  if (value >= 40) return "text-amber-400";
  return "text-rose-400";
}

function barTone(value: number): string {
  if (value >= 80) return "bg-emerald-500";
  if (value >= 60) return "bg-sky-500";
  if (value >= 40) return "bg-amber-500";
  return "bg-rose-500";
}

function chanceTone(chance: InterviewChance): string {
  if (chance === "high") return "bg-emerald-500/15 text-emerald-300 border-emerald-500/40";
  if (chance === "medium") return "bg-amber-500/15 text-amber-300 border-amber-500/40";
  return "bg-rose-500/15 text-rose-300 border-rose-500/40";
}

function MetricBar({ label, value }: { label: string; value: number }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className="space-y-1">
      <div className="flex items-baseline justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className={cn("text-base font-semibold tabular-nums", pctTone(value))}>
          {value}%
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={cn("h-full rounded-full", barTone(value))}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function ConfidencePanelCard({
  report,
  isLoading,
  hasAnalysis,
}: {
  report: JobConfidenceReport | undefined;
  isLoading: boolean;
  hasAnalysis: boolean;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Gauge className="h-4 w-4 text-primary" />
          Proposal confidence
        </CardTitle>
        <CardDescription className="text-xs">
          Multi-dimensional fit signal — derived from analyzer skills, portfolio + repo matches,
          and the opportunity score.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!hasAnalysis ? (
          <div className="text-sm text-muted-foreground">
            Run <span className="font-medium text-foreground">Analyze job</span> first — confidence
            uses the extracted skills + portfolio matches.
          </div>
        ) : isLoading || !report ? (
          <div className="text-sm text-muted-foreground">Computing confidence…</div>
        ) : (
          <>
            <div className="flex items-end justify-between gap-4 rounded-md border border-border/70 p-4">
              <div>
                <div className={cn("text-5xl font-semibold leading-none tabular-nums", pctTone(report.overall_match))}>
                  {report.overall_match}%
                </div>
                <div className="mt-1 text-xs uppercase tracking-wider text-muted-foreground">
                  Overall match
                </div>
              </div>
              <div
                className={cn(
                  "rounded-md border px-3 py-2 text-sm font-medium capitalize",
                  chanceTone(report.interview_chance),
                )}
                title="Bucketed from overall match + opportunity score"
              >
                Interview chance: {report.interview_chance}
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <MetricBar label="Technical" value={report.technical_match} />
              <MetricBar label="Domain" value={report.domain_match} />
              <MetricBar label="Architecture" value={report.architecture_match} />
            </div>

            {report.missing_critical_skills.length > 0 && (
              <div className="text-sm">
                <span className="text-muted-foreground">Missing critical skills: </span>
                {report.missing_critical_skills.map((s) => (
                  <span
                    key={s}
                    className="mr-1 rounded-md border border-rose-500/30 bg-rose-500/10 px-1.5 py-0.5 text-xs text-rose-300"
                  >
                    {s}
                  </span>
                ))}
              </div>
            )}

            {report.rationale.length > 0 && (
              <ul className="list-disc space-y-0.5 pl-5 text-sm text-muted-foreground">
                {report.rationale.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
