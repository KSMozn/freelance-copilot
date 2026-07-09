import { ExternalLink, Lightbulb, Loader2, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { cn } from "@/shared/lib/utils";
import type { PortfolioMatch, PortfolioMatchesResponse } from "@/features/professional/apiTypes";

function pctColor(score: number): string {
  if (score >= 0.7) return "text-emerald-400";
  if (score >= 0.5) return "text-blue-400";
  if (score >= 0.3) return "text-amber-400";
  return "text-rose-400";
}

function pct(score: number): string {
  return `${Math.round(score * 100)}%`;
}

function MatchRow({ match }: { match: PortfolioMatch }) {
  return (
    <div className="rounded-md border border-border/70 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <Link
            to={`/portfolio/${match.portfolio_id}`}
            className="block truncate text-base font-medium hover:underline"
          >
            {match.title}
          </Link>
          <div className="mt-1 flex flex-wrap gap-1.5">
            {match.relevant_domains.map((d) => (
              <Badge key={d} variant="secondary">
                {d}
              </Badge>
            ))}
            {match.relevant_skills.slice(0, 6).map((s) => (
              <Badge key={s} variant="outline">
                {s}
              </Badge>
            ))}
          </div>
        </div>
        <div className="text-right">
          <div className={cn("text-2xl font-semibold tabular-nums", pctColor(match.match_score))}>
            {pct(match.match_score)}
          </div>
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
            match
          </div>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-4 gap-2 text-[10px] uppercase tracking-wider text-muted-foreground">
        <Component label="semantic" value={match.semantic_score} />
        <Component label="skills" value={match.skill_overlap_score} />
        <Component label="domain" value={match.domain_overlap_score} />
        <Component label="strategic" value={match.strategic_score} />
      </div>

      {match.match_reasons.length > 0 && (
        <ul className="mt-3 list-disc space-y-0.5 pl-5 text-sm">
          {match.match_reasons.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      )}

      {match.suggested_talking_points.length > 0 && (
        <div className="mt-3 rounded-md bg-muted/40 p-3">
          <div className="mb-1.5 flex items-center gap-1.5 text-xs uppercase tracking-wide text-muted-foreground">
            <Lightbulb className="h-3.5 w-3.5" /> Talking points
          </div>
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {match.suggested_talking_points.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-3 flex justify-end">
        <Button asChild size="sm" variant="ghost">
          <Link to={`/portfolio/${match.portfolio_id}`}>
            Open project
            <ExternalLink className="ml-1 h-3.5 w-3.5" />
          </Link>
        </Button>
      </div>
    </div>
  );
}

function Component({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="text-foreground/80 tabular-nums">{pct(value)}</div>
      <div>{label}</div>
    </div>
  );
}

export function PortfolioMatchesCard({
  data,
  isPending,
  hasAnalysis,
  onRun,
}: {
  data: PortfolioMatchesResponse | undefined;
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
            Portfolio matches
          </CardTitle>
          <CardDescription className="text-xs">
            {data
              ? `Top ${data.matches.length} of ${data.portfolio_count} · ${data.embedding_provider} · ${data.embedding_model}`
              : "Rank your portfolio projects against this job."}
          </CardDescription>
        </div>
        <Button onClick={onRun} disabled={!hasAnalysis || isPending} size="sm">
          {isPending ? (
            <>
              <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
              Matching…
            </>
          ) : data ? (
            "Re-match"
          ) : (
            "Match portfolio"
          )}
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {!hasAnalysis ? (
          <div className="text-sm text-muted-foreground">
            Run <span className="font-medium text-foreground">Analyze job</span> first — matching
            uses the extracted skills, technologies, and domain.
          </div>
        ) : !data ? (
          <div className="text-sm text-muted-foreground">
            Click <span className="font-medium text-foreground">Match portfolio</span> to compare
            this job against your projects.
          </div>
        ) : data.matches.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            No portfolio projects yet — add some on the{" "}
            <Link to="/portfolio" className="text-primary hover:underline">
              Portfolio
            </Link>{" "}
            page.
          </div>
        ) : (
          data.matches.map((m) => <MatchRow key={m.portfolio_id} match={m} />)
        )}
      </CardContent>
    </Card>
  );
}
