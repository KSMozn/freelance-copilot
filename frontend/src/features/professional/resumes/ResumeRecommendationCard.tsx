import { ExternalLink, FileText, Lightbulb, Loader2, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { cn } from "@/shared/lib/utils";
import type {
  ResumeRecommendation,
  ResumeRecommendationsResponse,
} from "@/features/professional/apiTypes";

function pctColor(score: number): string {
  if (score >= 0.7) return "text-emerald-400";
  if (score >= 0.55) return "text-blue-400";
  if (score >= 0.4) return "text-amber-400";
  return "text-rose-400";
}

function pct(score: number): string {
  return `${Math.round(score * 100)}%`;
}

function Component({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="tabular-nums text-foreground/80">{pct(value)}</div>
      <div>{label}</div>
    </div>
  );
}

function RecommendationRow({ rec, isTop }: { rec: ResumeRecommendation; isTop: boolean }) {
  return (
    <div
      className={cn(
        "rounded-md border p-4",
        isTop ? "border-primary/50 bg-primary/5" : "border-border/70",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <Link
            to={`/resumes/${rec.resume_id}`}
            className="flex items-center gap-2 text-base font-medium hover:underline"
          >
            <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
            <span className="truncate">{rec.title}</span>
            {isTop && (
              <Badge variant="default" className="ml-1">
                Recommended
              </Badge>
            )}
          </Link>
        </div>
        <div className="text-right">
          <div className={cn("text-2xl font-semibold tabular-nums", pctColor(rec.match_score))}>
            {pct(rec.match_score)}
          </div>
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">match</div>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-4 gap-2 text-[10px] uppercase tracking-wider text-muted-foreground">
        <Component label="semantic" value={rec.semantic_score} />
        <Component label="skills" value={rec.skill_overlap_score} />
        <Component label="domain" value={rec.domain_overlap_score} />
        <Component label="seniority" value={rec.seniority_alignment_score} />
      </div>

      {rec.relevant_skills.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {rec.relevant_skills.map((s) => (
            <Badge key={s} variant="outline">
              {s}
            </Badge>
          ))}
        </div>
      )}

      {rec.fit_reasons.length > 0 && (
        <ul className="mt-3 list-disc space-y-0.5 pl-5 text-sm">
          {rec.fit_reasons.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      )}

      {rec.missing_or_weak_skills.length > 0 && (
        <div className="mt-3 text-sm">
          <span className="text-xs uppercase tracking-wider text-amber-400">Missing / weak:</span>{" "}
          <span className="text-muted-foreground">{rec.missing_or_weak_skills.join(", ")}</span>
        </div>
      )}

      {rec.suggested_positioning.length > 0 && (
        <div className="mt-3 rounded-md bg-muted/40 p-3">
          <div className="mb-1.5 flex items-center gap-1.5 text-xs uppercase tracking-wide text-muted-foreground">
            <Lightbulb className="h-3.5 w-3.5" /> Suggested positioning
          </div>
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {rec.suggested_positioning.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-3 flex justify-end">
        <Button asChild size="sm" variant="ghost">
          <Link to={`/resumes/${rec.resume_id}`}>
            Open resume
            <ExternalLink className="ml-1 h-3.5 w-3.5" />
          </Link>
        </Button>
      </div>
    </div>
  );
}

export function ResumeRecommendationCard({
  data,
  isPending,
  hasAnalysis,
  onRun,
}: {
  data: ResumeRecommendationsResponse | undefined;
  isPending: boolean;
  hasAnalysis: boolean;
  onRun: () => void;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            <Sparkles className="h-4 w-4 text-primary" />
            Recommended resume
          </CardTitle>
          <CardDescription className="text-xs">
            {data
              ? `Top ${data.recommendations.length} of ${data.resume_count} · ${data.embedding_provider} · ${data.embedding_model}`
              : "Rank your resume profiles for this job."}
          </CardDescription>
        </div>
        <Button onClick={onRun} disabled={!hasAnalysis || isPending} size="sm">
          {isPending ? (
            <>
              <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
              Ranking…
            </>
          ) : data ? (
            "Re-recommend"
          ) : (
            "Recommend resume"
          )}
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {!hasAnalysis ? (
          <div className="text-sm text-muted-foreground">
            Run <span className="font-medium text-foreground">Analyze job</span> first.
          </div>
        ) : !data ? (
          <div className="text-sm text-muted-foreground">
            Click <span className="font-medium text-foreground">Recommend resume</span> to rank your
            resume profiles against this job.
          </div>
        ) : data.recommendations.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            No resume profiles yet — add some on the{" "}
            <Link to="/resumes" className="text-primary hover:underline">
              Resumes
            </Link>{" "}
            page.
          </div>
        ) : (
          data.recommendations.map((rec, i) => (
            <RecommendationRow key={rec.resume_id} rec={rec} isTop={i === 0} />
          ))
        )}
      </CardContent>
    </Card>
  );
}
