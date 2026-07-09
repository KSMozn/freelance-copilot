import { Check, ExternalLink, FileCode2, Github, Lightbulb, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { cn } from "@/shared/lib/utils";
import type { RepositoryMatch, RepositoryMatchesResponse } from "@/types/api";

function pctColor(score: number): string {
  if (score >= 0.7) return "text-emerald-400";
  if (score >= 0.5) return "text-blue-400";
  if (score >= 0.3) return "text-amber-400";
  return "text-rose-400";
}

function pct(score: number): string {
  return `${Math.round(score * 100)}%`;
}

function Component({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="text-foreground/80 tabular-nums">{pct(value)}</div>
      <div>{label}</div>
    </div>
  );
}

function MatchRow({ match }: { match: RepositoryMatch }) {
  return (
    <div className="rounded-md border border-border/70 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <a
            href={match.github_url}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 text-base font-medium hover:underline"
          >
            <Github className="h-4 w-4 shrink-0" />
            <span className="truncate">
              {match.owner}/{match.name}
            </span>
          </a>
          <div className="mt-1 flex flex-wrap gap-1.5">
            {match.relevant_domains.map((d) => (
              <Badge key={d} variant="secondary">
                {d}
              </Badge>
            ))}
          </div>
          {match.matched_skills.length > 0 && (
            <div className="mt-2 space-y-0.5">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                Relevant because
              </div>
              <ul className="flex flex-wrap gap-x-3 gap-y-0.5 text-sm">
                {match.matched_skills.map((s) => (
                  <li key={s} className="flex items-center gap-1 text-emerald-400">
                    <Check className="h-3.5 w-3.5 shrink-0" />
                    <span className="text-foreground">{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        <div className="text-right">
          <div className={cn("text-2xl font-semibold tabular-nums", pctColor(match.match_score))}>
            {pct(match.match_score)}
          </div>
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">match</div>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-4 gap-2 text-[10px] uppercase tracking-wider text-muted-foreground">
        <Component label="semantic" value={match.semantic_score} />
        <Component label="skills" value={match.skill_overlap_score} />
        <Component label="domain" value={match.domain_overlap_score} />
        <Component label="architecture" value={match.architecture_score} />
      </div>

      {match.match_reasons.length > 0 && (
        <ul className="mt-3 list-disc space-y-0.5 pl-5 text-sm">
          {match.match_reasons.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      )}

      {match.relevant_paths.length > 0 && (
        <div className="mt-3 space-y-1">
          <div className="flex items-center gap-1.5 text-xs uppercase tracking-wide text-muted-foreground">
            <FileCode2 className="h-3.5 w-3.5" /> Relevant files
          </div>
          <ul className="space-y-0.5 text-xs font-mono">
            {match.relevant_paths.map((p) => (
              <li key={p}>
                <a
                  href={`${match.github_url}/blob/HEAD/${p}`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-primary hover:underline"
                  title={p}
                >
                  {p}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {match.missing_skills.length > 0 && (
        <div className="mt-3 text-xs">
          <span className="text-muted-foreground">Missing in this repo: </span>
          {match.missing_skills.slice(0, 8).map((s) => (
            <span
              key={s}
              className="mr-1 rounded-md border border-rose-500/30 px-1.5 py-0.5 text-rose-400"
            >
              {s}
            </span>
          ))}
        </div>
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
          <a href={match.github_url} target="_blank" rel="noreferrer">
            Open on GitHub
            <ExternalLink className="ml-1 h-3.5 w-3.5" />
          </a>
        </Button>
      </div>
    </div>
  );
}

export function RepositoryMatchesCard({
  data,
  isPending,
  hasAnalysis,
  onRun,
}: {
  data: RepositoryMatchesResponse | undefined;
  isPending: boolean;
  hasAnalysis: boolean;
  onRun: () => void;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            <Github className="h-4 w-4 text-primary" />
            Repository matches
          </CardTitle>
          <CardDescription className="text-xs">
            {data
              ? `Top ${data.matches.length} of ${data.repository_count} · ${data.embedding_provider} · ${data.embedding_model}`
              : "Rank your scanned GitHub repos against this job."}
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
            "Match repositories"
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
            Click <span className="font-medium text-foreground">Match repositories</span> to
            compare this job against your scanned repos.
          </div>
        ) : data.matches.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            No scanned repositories yet — add some on the{" "}
            <Link to="/repositories" className="text-primary hover:underline">
              Repositories
            </Link>{" "}
            page.
          </div>
        ) : (
          data.matches.map((m) => <MatchRow key={m.repository_id} match={m} />)
        )}
      </CardContent>
    </Card>
  );
}
