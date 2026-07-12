import {
  AlertTriangle,
  CheckCircle2,
  Copy,
  FileText,
  Loader2,
  RefreshCw,
  Save,
  Send,
  Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Textarea } from "@/shared/ui/textarea";
import {
  useApplicationForJob,
  useCreateApplicationFromProposal,
} from "@/features/professional/applications/applicationsApi";
import { cn } from "@/shared/lib/utils";
import {
  useGenerateProposal,
  useLatestProposal,
  useReviewProposal,
  useUpdateProposal,
} from "@/features/professional/proposals/proposalsApi";
import {
  PROPOSAL_ANGLE_LABELS,
  PROPOSAL_DIMENSION_LABELS,
  PROPOSAL_DIMENSION_MAX,
  type ImplementationWeek,
  type Proposal,
  type ProposalDiagram,
  type ProposalMilestone,
  type ProposalQualityBreakdown,
  type ProposalStrategy,
} from "@/features/professional/apiTypes";
import { MermaidDiagram } from "@/features/professional/proposals/MermaidDiagram";

const DIMENSION_ORDER: (keyof ProposalQualityBreakdown)[] = [
  "specificity",
  "relevance",
  "portfolio_evidence",
  "clarity",
  "brevity",
  "non_generic_wording",
  "risk_awareness",
  "call_to_action",
];

function scoreColor(score: number): string {
  if (score >= 85) return "text-emerald-400";
  if (score >= 70) return "text-blue-400";
  if (score >= 50) return "text-amber-400";
  return "text-rose-400";
}

function DiagramsCard({ diagrams }: { diagrams: ProposalDiagram[] }) {
  if (!diagrams.length) return null;
  return (
    <Card className="md:col-span-2">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Architecture diagrams</CardTitle>
        <CardDescription className="text-xs">
          Rendered from Mermaid sources — paste into any Mermaid-capable tool to re-render.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {diagrams.map((d, idx) => (
          <div key={`${d.kind}-${idx}`} className="space-y-2">
            <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
              <span className="rounded-md border border-primary/40 bg-primary/10 px-1.5 py-0.5 text-[10px] text-primary">
                {d.kind}
              </span>
              <span>{d.title}</span>
            </div>
            <MermaidDiagram source={d.mermaid} />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function ImplementationPlanCard({ weeks }: { weeks: ImplementationWeek[] }) {
  if (!weeks.length) return null;
  const sorted = [...weeks].sort((a, b) => a.week - b.week);
  return (
    <Card className="md:col-span-2">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Implementation plan</CardTitle>
        <CardDescription className="text-xs">
          Calendar view — distinct from the milestones above, which drive Upwork payments.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ol className="relative space-y-3 border-l border-border/70 pl-4">
          {sorted.map((w) => (
            <li key={w.week} className="relative">
              <span className="absolute -left-[1.45rem] top-0.5 flex h-5 w-5 items-center justify-center rounded-full border border-primary/50 bg-primary/10 text-[10px] font-semibold text-primary">
                {w.week}
              </span>
              <div className="text-sm font-medium">
                Week {w.week} — <span className="text-primary">{w.focus}</span>
              </div>
              <div className="mt-0.5 text-sm text-muted-foreground">{w.summary}</div>
              {w.deliverables.length > 0 && (
                <ul className="ml-4 mt-1 list-disc space-y-0.5 text-xs text-foreground/90">
                  {w.deliverables.map((d) => (
                    <li key={d}>{d}</li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}

function StrategyPanel({ strategy }: { strategy: ProposalStrategy }) {
  return (
    <div className="rounded-md border border-primary/30 bg-primary/5 p-3">
      <div className="mb-1 flex items-center gap-2 text-xs uppercase tracking-wide text-primary">
        <Sparkles className="h-3.5 w-3.5" /> Proposal strategy
        <span className="rounded-md border border-primary/40 bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium normal-case tracking-normal">
          {PROPOSAL_ANGLE_LABELS[strategy.angle]}
        </span>
      </div>
      <p className="text-sm">{strategy.rationale}</p>
      {strategy.emphasis_points.length > 0 && (
        <ul className="mt-2 list-disc space-y-0.5 pl-5 text-sm text-muted-foreground">
          {strategy.emphasis_points.map((p) => (
            <li key={p}>{p}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function QualityBars({ breakdown }: { breakdown: ProposalQualityBreakdown }) {
  return (
    <div className="space-y-2">
      {DIMENSION_ORDER.map((d) => {
        const value = breakdown[d];
        const max = PROPOSAL_DIMENSION_MAX[d];
        const pct = Math.max(0, Math.min(100, (value / max) * 100));
        return (
          <div key={d} className="space-y-1">
            <div className="flex items-baseline justify-between text-xs">
              <span className="text-muted-foreground">{PROPOSAL_DIMENSION_LABELS[d]}</span>
              <span className="tabular-nums">
                <span className="font-medium">{value}</span>
                <span className="text-muted-foreground"> / {max}</span>
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
              <div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

async function copyText(text: string, label: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
    toast.success(`Copied ${label}`);
  } catch {
    toast.error("Clipboard not available");
  }
}

function ProposalView({ jobId, proposal }: { jobId: string; proposal: Proposal }) {
  const [title, setTitle] = useState(proposal.title ?? "");
  const [body, setBody] = useState(proposal.body);
  const [shortBody, setShortBody] = useState(proposal.short_body ?? "");
  const [dirty, setDirty] = useState(false);

  // Reset local state when a different proposal arrives (e.g. after re-generate)
  useEffect(() => {
    setTitle(proposal.title ?? "");
    setBody(proposal.body);
    setShortBody(proposal.short_body ?? "");
    setDirty(false);
  }, [proposal.id, proposal.title, proposal.body, proposal.short_body]);

  const update = useUpdateProposal(jobId, proposal.id);
  const review = useReviewProposal(jobId, proposal.id);
  const existingApp = useApplicationForJob(jobId);
  const createApp = useCreateApplicationFromProposal(jobId);
  const linkedApp = existingApp.data;
  const linkedActive =
    linkedApp && !["rejected", "withdrawn", "completed"].includes(linkedApp.status);

  const save = () =>
    update.mutate(
      { title, body, short_body: shortBody },
      {
        onSuccess: () => {
          setDirty(false);
          toast.success("Proposal saved");
        },
        onError: () => toast.error("Could not save"),
      },
    );

  const rerun = () =>
    review.mutate(undefined, {
      onSuccess: (r) => toast.success(`Re-reviewed — score ${r.quality_score}/100`),
      onError: () => toast.error("Review failed"),
    });

  return (
    <div className="space-y-4">
      {proposal.quality_score !== null && proposal.quality_breakdown && (
        <div className="grid gap-4 rounded-md border border-border/70 p-4 md:grid-cols-[auto_1fr]">
          <div className="text-center md:text-left">
            <div
              className={cn(
                "text-5xl font-semibold tabular-nums leading-none",
                scoreColor(proposal.quality_score),
              )}
            >
              {proposal.quality_score}
            </div>
            <div className="mt-1 text-xs text-muted-foreground">quality / 100</div>
            <div className="mt-2 text-[10px] uppercase tracking-wider text-muted-foreground">
              {proposal.model_provider} · {proposal.model_name}
            </div>
          </div>
          <QualityBars breakdown={proposal.quality_breakdown} />
        </div>
      )}

      {proposal.quality_warnings.length > 0 && (
        <div className="rounded-md border border-amber-500/30 bg-amber-500/5 p-3">
          <div className="mb-1 flex items-center gap-1.5 text-xs uppercase tracking-wide text-amber-400">
            <AlertTriangle className="h-3.5 w-3.5" /> Review warnings
          </div>
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {proposal.quality_warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {proposal.strategy && <StrategyPanel strategy={proposal.strategy} />}

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="proposal-title">Headline</Label>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => copyText(title || proposal.title || "", "headline")}
          >
            <Copy className="mr-1 h-3.5 w-3.5" />
            Copy
          </Button>
        </div>
        <Input
          id="proposal-title"
          value={title}
          onChange={(e) => {
            setTitle(e.target.value);
            setDirty(true);
          }}
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="proposal-body">Body</Label>
          <div className="flex gap-1">
            <span className="text-xs text-muted-foreground">
              {body.split(/\s+/).filter(Boolean).length} words
            </span>
            <Button size="sm" variant="ghost" onClick={() => copyText(body, "body")}>
              <Copy className="mr-1 h-3.5 w-3.5" />
              Copy
            </Button>
          </div>
        </div>
        <Textarea
          id="proposal-body"
          rows={12}
          value={body}
          onChange={(e) => {
            setBody(e.target.value);
            setDirty(true);
          }}
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="proposal-short">Short version</Label>
          <div className="flex gap-1">
            <span className="text-xs text-muted-foreground">
              {shortBody.split(/\s+/).filter(Boolean).length} words
            </span>
            <Button size="sm" variant="ghost" onClick={() => copyText(shortBody, "short version")}>
              <Copy className="mr-1 h-3.5 w-3.5" />
              Copy
            </Button>
          </div>
        </div>
        <Textarea
          id="proposal-short"
          rows={6}
          value={shortBody}
          onChange={(e) => {
            setShortBody(e.target.value);
            setDirty(true);
          }}
        />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Button onClick={save} disabled={!dirty || update.isPending}>
          {update.isPending ? (
            <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
          ) : (
            <Save className="mr-2 h-3.5 w-3.5" />
          )}
          Save changes
        </Button>
        <Button variant="outline" onClick={rerun} disabled={review.isPending}>
          {review.isPending ? (
            <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-3.5 w-3.5" />
          )}
          Re-run review
        </Button>
        {linkedActive ? (
          <Button asChild variant="secondary">
            <Link to={`/applications/${linkedApp!.id}`}>
              <CheckCircle2 className="mr-2 h-3.5 w-3.5" />
              Applied · {linkedApp!.status}
            </Link>
          </Button>
        ) : (
          <Button
            variant="default"
            disabled={createApp.isPending}
            onClick={() =>
              createApp.mutate(proposal.id, {
                onSuccess: () => toast.success("Application created"),
                onError: (err: unknown) => {
                  const detail =
                    (err as { response?: { data?: { detail?: string } } } | undefined)?.response
                      ?.data?.detail ?? "Could not create application";
                  toast.error(detail);
                },
              })
            }
          >
            {createApp.isPending ? (
              <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
            ) : (
              <Send className="mr-2 h-3.5 w-3.5" />
            )}
            Mark as Applied
          </Button>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {proposal.questions.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Questions for the client</CardTitle>
            </CardHeader>
            <CardContent>
              <ol className="list-decimal space-y-1 pl-5 text-sm">
                {proposal.questions.map((q) => (
                  <li key={q}>{q}</li>
                ))}
              </ol>
            </CardContent>
          </Card>
        )}
        {proposal.delivery_approach.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Delivery approach</CardTitle>
            </CardHeader>
            <CardContent>
              <ol className="list-decimal space-y-1 pl-5 text-sm">
                {proposal.delivery_approach.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ol>
            </CardContent>
          </Card>
        )}
        {proposal.milestones.length > 0 && (
          <Card className="md:col-span-2">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Milestones</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                {proposal.milestones.map((m: ProposalMilestone) => (
                  <li key={m.name} className="rounded-md border border-border/70 p-3">
                    <div className="flex items-baseline justify-between gap-2">
                      <span className="font-medium">{m.name}</span>
                      {m.estimated_hours != null && (
                        <Badge variant="outline">{m.estimated_hours}h</Badge>
                      )}
                    </div>
                    <div className="mt-1 text-muted-foreground">{m.description}</div>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
        <ImplementationPlanCard weeks={proposal.implementation_plan} />
        <DiagramsCard diagrams={proposal.diagrams} />
        {proposal.risk_notes.length > 0 && (
          <Card className="md:col-span-2">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Risk notes</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc space-y-1 pl-5 text-sm">
                {proposal.risk_notes.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export function ProposalCard({
  jobId,
  hasAnalysis,
}: {
  jobId: string | undefined;
  hasAnalysis: boolean;
}) {
  const { data: proposal, isLoading } = useLatestProposal(jobId);
  const generate = useGenerateProposal(jobId);

  const onGenerate = () =>
    generate.mutate(undefined, {
      onSuccess: (p) => toast.success(`Proposal generated — quality ${p.quality_score ?? "—"}/100`),
      onError: (err: unknown) => {
        const detail =
          (err as { response?: { data?: { detail?: string } } } | undefined)?.response?.data
            ?.detail ?? "Generation failed";
        toast.error(detail);
      },
    });

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            <FileText className="h-4 w-4 text-primary" />
            Proposal
          </CardTitle>
          <CardDescription className="text-xs">
            {proposal
              ? `Generated ${proposal.created_at ? new Date(proposal.created_at).toLocaleString() : ""} · prompt ${proposal.prompt_version ?? "?"}`
              : "Generate a tailored proposal grounded in the analysis + matched portfolio + recommended resume."}
          </CardDescription>
        </div>
        <Button onClick={onGenerate} disabled={!hasAnalysis || generate.isPending} size="sm">
          {generate.isPending ? (
            <>
              <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
              Generating…
            </>
          ) : proposal ? (
            <>
              <Sparkles className="mr-2 h-3.5 w-3.5" />
              Regenerate
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-3.5 w-3.5" />
              Generate proposal
            </>
          )}
        </Button>
      </CardHeader>
      <CardContent>
        {!hasAnalysis ? (
          <div className="text-sm text-muted-foreground">
            Run <span className="font-medium text-foreground">Analyze job</span> first — the
            proposal needs the structured analysis to ground itself.
          </div>
        ) : isLoading ? (
          <div className="text-sm text-muted-foreground">Checking for existing proposal…</div>
        ) : !proposal ? (
          <div className="text-sm text-muted-foreground">
            No proposal yet. Click{" "}
            <span className="font-medium text-foreground">Generate proposal</span> to draft one from
            the analysis, top portfolio matches, and recommended resume.
          </div>
        ) : jobId ? (
          <ProposalView jobId={jobId} proposal={proposal} />
        ) : null}
      </CardContent>
    </Card>
  );
}
