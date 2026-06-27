import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, RefreshCw, Sparkles, Trash2 } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";

import {
  ExtractionCard,
  FlagsCard,
  QuestionsCard,
  RisksCard,
  SummaryCard,
} from "@/components/analysis/AnalysisSections";
import { ScoreBreakdown } from "@/components/analysis/ScoreBreakdown";
import { ScoreCard } from "@/components/analysis/ScoreCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { useAnalyzeJob, useJobAnalysis } from "@/lib/analysis";
import type { Job, JobStatus } from "@/types/api";

const NEXT_STATUSES: JobStatus[] = ["new", "shortlisted", "applied", "ignored", "archived"];

export function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: job, isLoading } = useQuery({
    queryKey: ["job", id],
    queryFn: async () => {
      const { data } = await api.get<Job>(`/jobs/${id}`);
      return data;
    },
    enabled: !!id,
  });

  const { data: analysisData, isLoading: analysisLoading } = useJobAnalysis(id);
  const analyze = useAnalyzeJob(id);

  const statusMutation = useMutation({
    mutationFn: async (status: JobStatus) => {
      const { data } = await api.patch<Job>(`/jobs/${id}`, { status });
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["job", id] });
      qc.invalidateQueries({ queryKey: ["jobs"] });
      toast.success("Status updated");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async () => {
      await api.delete(`/jobs/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      toast.success("Job deleted");
      navigate("/jobs");
    },
  });

  const runAnalyze = () =>
    analyze.mutate(undefined, {
      onSuccess: () => toast.success("Analysis complete"),
      onError: (err: unknown) => {
        const detail =
          (err as { response?: { data?: { detail?: string } } } | undefined)?.response?.data?.detail ??
          "Analysis failed";
        toast.error(detail);
      },
    });

  if (isLoading) return <div className="text-sm text-muted-foreground">Loading…</div>;
  if (!job) return <div className="text-sm text-muted-foreground">Job not found.</div>;

  const analysis = analysisData?.analysis;
  const score = analysisData?.score;
  const hasAnalysis = !!analysis && !!score;

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="truncate text-2xl font-semibold tracking-tight">{job.title}</h1>
          <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
            <Badge variant="secondary">{job.status}</Badge>
            <span>v{job.version}</span>
            <span>·</span>
            <span>imported {new Date(job.imported_at).toLocaleString()}</span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button onClick={runAnalyze} disabled={analyze.isPending}>
            {analyze.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing…
              </>
            ) : hasAnalysis ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4" />
                Re-analyze
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Analyze job
              </>
            )}
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => {
              if (confirm("Delete this job?")) deleteMutation.mutate();
            }}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>
      </div>

      {analysisLoading && !hasAnalysis ? (
        <div className="text-sm text-muted-foreground">Checking for existing analysis…</div>
      ) : analyze.isPending && !hasAnalysis ? (
        <Card>
          <CardContent className="flex items-center gap-3 p-6 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Running analyzer + scoring engine…
          </CardContent>
        </Card>
      ) : hasAnalysis ? (
        <>
          <ScoreCard score={score} />
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="space-y-4 lg:col-span-2">
              <SummaryCard analysis={analysis} />
              <ExtractionCard analysis={analysis} />
              <RisksCard analysis={analysis} />
              <FlagsCard analysis={analysis} />
              <QuestionsCard analysis={analysis} />
            </div>
            <div className="space-y-4">
              <ScoreBreakdown breakdown={score.score_breakdown} />
            </div>
          </div>
        </>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">No analysis yet</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Click <span className="font-medium text-foreground">Analyze job</span> to extract structured
            information and compute an opportunity score. No data leaves your machine unless you have
            configured a real AI provider.
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Status</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {NEXT_STATUSES.map((s) => (
            <Button
              key={s}
              size="sm"
              variant={job.status === s ? "default" : "outline"}
              onClick={() => statusMutation.mutate(s)}
              disabled={statusMutation.isPending}
            >
              {s}
            </Button>
          ))}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Budget</CardTitle>
          </CardHeader>
          <CardContent className="text-sm">
            <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-1">
              <dt className="text-muted-foreground">Type</dt>
              <dd>{job.budget_type ?? "—"}</dd>
              <dt className="text-muted-foreground">Currency</dt>
              <dd>{job.currency}</dd>
              <dt className="text-muted-foreground">Min</dt>
              <dd>{job.budget_min ?? "—"}</dd>
              <dt className="text-muted-foreground">Max</dt>
              <dd>{job.budget_max ?? "—"}</dd>
            </dl>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Competition</CardTitle>
          </CardHeader>
          <CardContent className="text-sm">
            <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-1">
              <dt className="text-muted-foreground">Proposals</dt>
              <dd>{job.proposal_count ?? "—"}</dd>
              <dt className="text-muted-foreground">Source URL</dt>
              <dd className="truncate">
                {job.source_url ? (
                  <a className="text-primary hover:underline" href={job.source_url} target="_blank" rel="noreferrer">
                    {job.source_url}
                  </a>
                ) : (
                  "—"
                )}
              </dd>
            </dl>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Original description</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-relaxed text-foreground">
            {job.description}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
