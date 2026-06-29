import { Award, BookOpen, GitPullRequest, Lightbulb, RefreshCw, Star, Wrench } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  useMatchReport,
  useRebuildMatchReport,
  type GapRecommendation,
  type MatchReport,
  type RecommendationKind,
} from "@/lib/match-report";
import { useAuthStore } from "@/stores/auth";

interface Props {
  jobId: string;
}

/**
 * Persona-aware Match Report card. Renders the orchestrated output of
 * MatchReportService — base dimensions (technical / architecture / domain),
 * Phase E additions (leadership / soft, when scored), and the actionable
 * gap-recommendation list.
 *
 * The score is computed against the *active persona* (Phase C) — the chip
 * in the header makes the framing explicit so users always know which lens
 * the report represents.
 */
export function MatchReportCard({ jobId }: Props) {
  const activePersonaId = useAuthStore((s) => s.activePersonaId);
  const { data, isLoading, isError } = useMatchReport(jobId, activePersonaId);
  const rebuild = useRebuildMatchReport(jobId);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Match Report</CardTitle>
          <CardDescription>Computing per-persona match…</CardDescription>
        </CardHeader>
      </Card>
    );
  }
  if (isError || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Match Report</CardTitle>
          <CardDescription>
            Could not compute a report (analyse the job first).
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base flex items-center gap-2">
              Match Report
              <ChanceBadge chance={data.interview_chance} />
            </CardTitle>
            <CardDescription>
              {data.profile_version?.startsWith("persona:")
                ? "Scored against your active persona — switch personas to re-score."
                : "Scored against your default profile."}
            </CardDescription>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => rebuild.mutate(activePersonaId ?? null)}
            disabled={rebuild.isPending}
          >
            <RefreshCw className={`h-3 w-3 mr-1 ${rebuild.isPending ? "animate-spin" : ""}`} />
            Re-run
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <OverallScore data={data} />
        <DimensionGrid data={data} />
        <Recommendations recommendations={data.missing_recommendations} />
        {data.rationale.length > 0 && (
          <Rationale rationale={data.rationale} />
        )}
      </CardContent>
    </Card>
  );
}

// ---- Overall + dimensions -----------------------------------------------

function OverallScore({ data }: { data: MatchReport }) {
  const score = data.overall_match;
  return (
    <div className="flex items-end justify-between gap-4 pb-3 border-b">
      <div>
        <p className="text-xs uppercase tracking-wide text-muted-foreground">
          Overall match
        </p>
        <p className="text-4xl font-semibold tabular-nums">
          {score}
          <span className="text-xl text-muted-foreground">/100</span>
        </p>
      </div>
      <div className="text-right text-xs text-muted-foreground">
        {data.missing_critical_skills.length} missing critical skill
        {data.missing_critical_skills.length === 1 ? "" : "s"}
      </div>
    </div>
  );
}

function DimensionGrid({ data }: { data: MatchReport }) {
  const rows: { label: string; value: number | null }[] = [
    { label: "Technical fit", value: data.technical_fit },
    { label: "Architecture fit", value: data.architecture_fit },
    { label: "Domain fit", value: data.domain_fit },
    { label: "Leadership fit", value: data.leadership_fit },
    { label: "Soft-skills fit", value: data.soft_skills_fit },
  ];
  return (
    <div className="grid gap-2 md:grid-cols-2">
      {rows.map((row) => (
        <DimensionRow key={row.label} label={row.label} value={row.value} />
      ))}
    </div>
  );
}

function DimensionRow({ label, value }: { label: string; value: number | null }) {
  if (value === null) {
    return (
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="text-xs text-muted-foreground italic">
          not scored for this role
        </span>
      </div>
    );
  }
  const color =
    value >= 70 ? "bg-emerald-500" : value >= 40 ? "bg-amber-500" : "bg-destructive";
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span>{label}</span>
        <span className="tabular-nums font-medium">{value}</span>
      </div>
      <div className="h-1.5 bg-muted rounded-full overflow-hidden">
        <div
          className={`h-full ${color} transition-[width]`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

function ChanceBadge({ chance }: { chance: MatchReport["interview_chance"] }) {
  const cfg = {
    high: { label: "High chance", className: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300" },
    medium: { label: "Medium chance", className: "bg-amber-500/10 text-amber-700 dark:text-amber-300" },
    low: { label: "Low chance", className: "bg-destructive/10 text-destructive" },
  }[chance];
  return (
    <span
      className={`text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full ${cfg.className}`}
    >
      {cfg.label}
    </span>
  );
}

// ---- Recommendations -----------------------------------------------------

function Recommendations({ recommendations }: { recommendations: GapRecommendation[] }) {
  if (!recommendations.length) {
    return (
      <div className="text-sm text-muted-foreground">
        No gap recommendations — your graph already covers the critical skills.
      </div>
    );
  }
  return (
    <div className="space-y-2">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">
        Close the gap
      </p>
      <ul className="space-y-2">
        {recommendations.map((rec, i) => (
          <li
            key={`${rec.skill}-${rec.kind}-${i}`}
            className="rounded-md border bg-muted/30 p-3 text-sm space-y-1"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium flex items-center gap-2">
                <KindIcon kind={rec.kind} />
                {rec.skill}
              </span>
              <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
                {rec.effort_estimate}
              </span>
            </div>
            <p className="text-sm">{rec.suggestion}</p>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Badge variant="outline" className="text-[10px]">
                {kindLabel(rec.kind)}
              </Badge>
              <span>· Priority {rec.priority}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function KindIcon({ kind }: { kind: RecommendationKind }) {
  const Cmp = {
    project_to_build: Wrench,
    certification: Award,
    learning_resource: BookOpen,
    github_enhancement: GitPullRequest,
    experience_to_emphasize: Star,
  }[kind];
  return <Cmp className="h-4 w-4 text-primary" />;
}

function kindLabel(kind: RecommendationKind): string {
  return (
    {
      project_to_build: "Project",
      certification: "Cert",
      learning_resource: "Learn",
      github_enhancement: "GitHub",
      experience_to_emphasize: "Highlight",
    } as Record<RecommendationKind, string>
  )[kind];
}

function Rationale({ rationale }: { rationale: string[] }) {
  return (
    <div className="space-y-2">
      <p className="text-xs uppercase tracking-wide text-muted-foreground flex items-center gap-1">
        <Lightbulb className="h-3 w-3" />
        Rationale
      </p>
      <ul className="space-y-1">
        {rationale.map((line, i) => (
          <li key={i} className="text-sm text-muted-foreground">
            {line}
          </li>
        ))}
      </ul>
    </div>
  );
}
