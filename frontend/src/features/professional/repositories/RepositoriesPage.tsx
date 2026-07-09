import { FormEvent, useState } from "react";
import {
  ExternalLink,
  Github,
  Loader2,
  RefreshCw,
  Search,
  Sparkles,
  Trash2,
  Wrench,
} from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import {
  useDeleteRepository,
  useGenerateStarStory,
  useRegisterRepository,
  useRepositoryImprovements,
  useRepositoryList,
  useRescanRepository,
} from "@/features/professional/repositories/repositoriesApi";
import type {
  Repository,
  RepositoryImprovements as RepositoryImprovementsT,
  RepositoryScanStatus,
} from "@/features/professional/apiTypes";

function statusVariant(status: RepositoryScanStatus): "default" | "secondary" | "destructive" | "outline" {
  if (status === "scanned") return "default";
  if (status === "failed") return "destructive";
  return "secondary";
}

function TagList({ items, tone }: { items: string[]; tone?: string }) {
  if (!items.length) return null;
  return (
    <div className="flex flex-wrap gap-1">
      {items.slice(0, 12).map((s) => (
        <span
          key={s}
          className={`rounded-md border px-1.5 py-0.5 text-xs ${tone ?? "border-muted text-muted-foreground"}`}
        >
          {s}
        </span>
      ))}
      {items.length > 12 && (
        <span className="text-xs text-muted-foreground">+{items.length - 12} more</span>
      )}
    </div>
  );
}

function StarStorySection({ repo }: { repo: Repository }) {
  const generate = useGenerateStarStory();
  const canGenerate = repo.scan_status === "scanned";
  const story = repo.star_story;
  const run = () =>
    generate.mutate(repo.id, {
      onSuccess: () => toast.success(`STAR story ready for ${repo.owner}/${repo.name}`),
      onError: (err: unknown) => {
        const detail =
          (err as { response?: { data?: { detail?: string } } } | undefined)?.response?.data?.detail ??
          "STAR generation failed";
        toast.error(detail);
      },
    });

  return (
    <div className="space-y-2 rounded-md border border-primary/30 bg-primary/5 p-3">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-primary">
          <Sparkles className="h-3.5 w-3.5" /> STAR story
        </div>
        <Button
          size="sm"
          variant="ghost"
          disabled={!canGenerate || generate.isPending}
          onClick={run}
        >
          {generate.isPending ? (
            <>
              <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
              Generating…
            </>
          ) : story ? (
            <>
              <RefreshCw className="mr-1 h-3.5 w-3.5" />
              Regenerate
            </>
          ) : (
            <>
              <Sparkles className="mr-1 h-3.5 w-3.5" />
              Generate
            </>
          )}
        </Button>
      </div>
      {!canGenerate ? (
        <p className="text-xs text-muted-foreground">
          Scan the repo successfully before generating a STAR story.
        </p>
      ) : story ? (
        <div className="space-y-1.5 text-sm">
          <p className="font-medium text-foreground">{story.headline}</p>
          <dl className="grid grid-cols-[max-content_1fr] gap-x-3 gap-y-1 text-xs">
            <dt className="font-medium uppercase tracking-wide text-muted-foreground">Situation</dt>
            <dd>{story.situation}</dd>
            <dt className="font-medium uppercase tracking-wide text-muted-foreground">Task</dt>
            <dd>{story.task}</dd>
            <dt className="font-medium uppercase tracking-wide text-muted-foreground">Action</dt>
            <dd>{story.action}</dd>
            <dt className="font-medium uppercase tracking-wide text-muted-foreground">Result</dt>
            <dd>{story.result}</dd>
          </dl>
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">
          Generate an interview-ready Situation / Task / Action / Result story
          for this repo. Useful as a proposal hook + interview talking-point.
        </p>
      )}
    </div>
  );
}

function RepoCard({ repo }: { repo: Repository }) {
  const rescan = useRescanRepository();
  const del = useDeleteRepository();
  const isBusy = rescan.isPending || del.isPending;

  const totalBytes = Object.values(repo.languages).reduce((a, b) => a + b, 0) || 1;
  const langs = Object.entries(repo.languages)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 4)
    .map(([name, bytes]) => `${name} ${Math.round((bytes / totalBytes) * 100)}%`);

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
        <div className="min-w-0">
          <CardTitle className="flex items-center gap-2 text-base">
            <Github className="h-4 w-4 shrink-0" />
            <span className="truncate">
              {repo.owner}/{repo.name}
            </span>
            <Badge variant={statusVariant(repo.scan_status)} className="ml-2 capitalize">
              {repo.scan_status}
            </Badge>
          </CardTitle>
          {repo.description && (
            <p className="mt-1 truncate text-xs text-muted-foreground">{repo.description}</p>
          )}
        </div>
        <div className="flex gap-1">
          <Button asChild size="sm" variant="ghost">
            <a href={repo.github_url} target="_blank" rel="noreferrer">
              <ExternalLink className="h-4 w-4" />
            </a>
          </Button>
          <Button
            size="sm"
            variant="ghost"
            disabled={isBusy}
            onClick={() =>
              rescan.mutate(repo.id, {
                onSuccess: () => toast.success(`Re-scanned ${repo.owner}/${repo.name}`),
                onError: (err: unknown) => {
                  const detail =
                    (err as { response?: { data?: { detail?: string } } } | undefined)?.response?.data?.detail ??
                    "Rescan failed";
                  toast.error(detail);
                },
              })
            }
          >
            {rescan.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            disabled={isBusy}
            onClick={() => {
              if (confirm(`Delete ${repo.owner}/${repo.name}?`)) {
                del.mutate(repo.id, {
                  onSuccess: () => toast.success("Deleted"),
                });
              }
            }}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {repo.scan_status === "failed" && repo.scan_error && (
          <div className="rounded-md border border-destructive/40 bg-destructive/10 p-2 text-xs text-destructive">
            {repo.scan_error}
          </div>
        )}

        {repo.architecture_summary && (
          <p className="text-sm leading-relaxed text-foreground">{repo.architecture_summary}</p>
        )}

        {langs.length > 0 && (
          <div className="text-xs text-muted-foreground">{langs.join(" · ")}</div>
        )}

        <div className="grid gap-2 sm:grid-cols-2">
          {repo.frameworks.length > 0 && (
            <div className="space-y-1">
              <div className="text-xs font-medium text-muted-foreground">Frameworks</div>
              <TagList items={repo.frameworks} tone="border-primary/40 text-primary" />
            </div>
          )}
          {repo.databases.length > 0 && (
            <div className="space-y-1">
              <div className="text-xs font-medium text-muted-foreground">Databases</div>
              <TagList items={repo.databases} />
            </div>
          )}
          {repo.authentication.length > 0 && (
            <div className="space-y-1">
              <div className="text-xs font-medium text-muted-foreground">Authentication</div>
              <TagList items={repo.authentication} />
            </div>
          )}
          {repo.ai_providers.length > 0 && (
            <div className="space-y-1">
              <div className="text-xs font-medium text-muted-foreground">AI providers</div>
              <TagList items={repo.ai_providers} />
            </div>
          )}
          {repo.cloud.length > 0 && (
            <div className="space-y-1">
              <div className="text-xs font-medium text-muted-foreground">Cloud</div>
              <TagList items={repo.cloud} />
            </div>
          )}
          {repo.test_frameworks.length > 0 && (
            <div className="space-y-1">
              <div className="text-xs font-medium text-muted-foreground">Testing</div>
              <TagList items={repo.test_frameworks} />
            </div>
          )}
        </div>

        <div className="flex flex-wrap gap-3 text-xs">
          <span className={repo.has_docker ? "text-emerald-500" : "text-muted-foreground"}>
            {repo.has_docker ? "✓" : "·"} Docker
          </span>
          <span className={repo.has_ci ? "text-emerald-500" : "text-muted-foreground"}>
            {repo.has_ci ? "✓" : "·"} CI {repo.ci_systems.length > 0 && `(${repo.ci_systems.join(", ")})`}
          </span>
          <span className={repo.has_tests ? "text-emerald-500" : "text-muted-foreground"}>
            {repo.has_tests ? "✓" : "·"} Tests
          </span>
        </div>

        {repo.highlights.length > 0 && (
          <div className="space-y-1">
            <div className="text-xs font-medium text-muted-foreground">Highlights</div>
            <ul className="ml-4 list-disc space-y-0.5 text-xs text-foreground">
              {repo.highlights.slice(0, 4).map((h) => (
                <li key={h}>{h}</li>
              ))}
            </ul>
          </div>
        )}

        <StarStorySection repo={repo} />
      </CardContent>
    </Card>
  );
}

function ImprovementsBlock({ repo }: { repo: RepositoryImprovementsT }) {
  if (!repo.improvements.length) {
    return (
      <div className="text-xs text-muted-foreground">
        No high-frequency gaps — this repo covers the skills that show up in your analyzed jobs.
      </div>
    );
  }
  return (
    <ul className="space-y-1.5">
      {repo.improvements.map((imp) => {
        const pct = Math.round(imp.job_frequency_pct * 100);
        return (
          <li key={imp.skill} className="flex items-start justify-between gap-3 text-sm">
            <div className="min-w-0">
              <div className="font-medium">{imp.suggestion}</div>
              <div className="text-xs text-muted-foreground">
                <span className="rounded-md border border-muted px-1.5 py-0.5">
                  {imp.skill}
                </span>{" "}
                · {imp.job_frequency} jobs ({pct}%)
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function ImprovementsCard() {
  const { data, isLoading } = useRepositoryImprovements();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Wrench className="h-4 w-4 text-primary" />
          Suggested improvements
        </CardTitle>
        <CardDescription className="text-xs">
          {data
            ? `Per-repo gaps ranked by frequency across ${data.analyzed_job_count} analyzed jobs.`
            : "Per-repo gaps ranked by frequency across your analyzed jobs."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading || !data ? (
          <div className="text-sm text-muted-foreground">Building improvement report…</div>
        ) : data.analyzed_job_count === 0 ? (
          <div className="text-sm text-muted-foreground">
            No analyzed jobs yet — run <span className="font-medium text-foreground">Analyze job</span> on
            a few jobs first so we have a skill-frequency tally to compare against.
          </div>
        ) : !data.repositories.length ? (
          <div className="text-sm text-muted-foreground">
            No scanned repositories yet. Add one above to see suggestions.
          </div>
        ) : (
          data.repositories.map((repo) => (
            <div key={repo.repository_id} className="rounded-md border border-border/70 p-3">
              <a
                href={repo.github_url}
                target="_blank"
                rel="noreferrer"
                className="mb-2 flex items-center gap-2 text-sm font-medium hover:underline"
              >
                <Github className="h-3.5 w-3.5" />
                {repo.owner}/{repo.name}
              </a>
              <ImprovementsBlock repo={repo} />
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}


export function RepositoriesPage() {
  const [search, setSearch] = useState("");
  const [url, setUrl] = useState("");

  const { data, isLoading } = useRepositoryList({ search });
  const register = useRegisterRepository();

  const onAdd = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) return;
    register.mutate(trimmed, {
      onSuccess: (repo) => {
        setUrl("");
        if (repo.scan_status === "failed") {
          toast.warning(`Added ${repo.owner}/${repo.name}, but scan failed`);
        } else {
          toast.success(`Scanned ${repo.owner}/${repo.name}`);
        }
      },
      onError: (err: unknown) => {
        const detail =
          (err as { response?: { data?: { detail?: string } } } | undefined)?.response?.data?.detail ??
          "Failed to register repository";
        toast.error(detail);
      },
    });
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Repositories</h1>
        <p className="text-sm text-muted-foreground">
          Auto-scanned GitHub repositories. Used as concrete technical evidence when
          matching jobs.
        </p>
      </div>

      <Card>
        <CardContent className="p-4">
          <form onSubmit={onAdd} className="flex gap-2">
            <Input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/owner/repo"
              className="flex-1"
              disabled={register.isPending}
            />
            <Button type="submit" disabled={register.isPending || !url.trim()}>
              {register.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Scanning…
                </>
              ) : (
                <>
                  <Github className="mr-2 h-4 w-4" />
                  Add & scan
                </>
              )}
            </Button>
          </form>
          <p className="mt-2 text-xs text-muted-foreground">
            Public repos work without auth (rate-limited). Set <code>GITHUB_TOKEN</code> in
            <code> .env</code> for private repos and a higher rate budget.
          </p>
        </CardContent>
      </Card>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search repositories…"
          className="pl-9"
        />
      </div>

      {isLoading ? (
        <div className="text-sm text-muted-foreground">Loading…</div>
      ) : !data?.items.length ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            No repositories yet. Add one above — try a project you'd cite in a proposal.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {data.items.map((r) => (
            <RepoCard key={r.id} repo={r} />
          ))}
        </div>
      )}

      {!!data?.items.length && <ImprovementsCard />}
    </div>
  );
}
