import { AlertCircle, CheckCircle2, MinusCircle, Target } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { cn } from "@/shared/lib/utils";
import {
  STACK_CATEGORY_LABELS,
  type EvidenceReport,
  type SkillEvidence,
  type SkillEvidenceStatus,
} from "@/types/api";

const STATUS_ORDER: SkillEvidenceStatus[] = ["strong", "weak", "missing"];

const STATUS_META: Record<
  SkillEvidenceStatus,
  { label: string; tone: string; icon: typeof CheckCircle2 }
> = {
  strong: {
    label: "Strong matches",
    tone: "text-emerald-400",
    icon: CheckCircle2,
  },
  weak: {
    label: "Weak matches",
    tone: "text-amber-400",
    icon: AlertCircle,
  },
  missing: {
    label: "Missing skills",
    tone: "text-rose-400",
    icon: MinusCircle,
  },
};

const SOURCE_ABBREV: Record<string, string> = {
  portfolio: "PF",
  resume: "CV",
  repository: "REPO",
};

function Stars({ importance }: { importance: number | null }) {
  if (!importance) return null;
  return (
    <span className="font-mono text-[10px] tabular-nums">
      <span className="text-primary">{"★".repeat(importance)}</span>
      <span className="text-muted-foreground/40">{"★".repeat(5 - importance)}</span>
    </span>
  );
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.max(0, Math.min(100, confidence * 100));
  const tone =
    confidence >= 0.7 ? "bg-emerald-500" : confidence >= 0.4 ? "bg-amber-500" : "bg-rose-500";
  return (
    <div className="flex items-center gap-1.5">
      <div className="h-1 w-16 overflow-hidden rounded-full bg-muted">
        <div className={cn("h-full rounded-full", tone)} style={{ width: `${pct}%` }} />
      </div>
      <span className="font-mono text-[10px] tabular-nums text-muted-foreground">
        {Math.round(pct)}%
      </span>
    </div>
  );
}

function SkillRow({ skill }: { skill: SkillEvidence }) {
  const sources = Array.from(new Set(skill.evidence.map((e) => e.source_type)));
  return (
    <li className="rounded-md border border-border/70 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium">{skill.name}</span>
            {skill.category && (
              <span className="rounded-md border border-muted px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
                {STACK_CATEGORY_LABELS[skill.category]}
              </span>
            )}
            <Stars importance={skill.importance} />
          </div>
          {skill.best_snippet ? (
            <p className="mt-1 text-sm text-foreground/90">{skill.best_snippet}</p>
          ) : (
            <p className="mt-1 text-sm italic text-muted-foreground">
              No matching evidence in portfolios, resume, or scanned repos — call this out as a gap.
            </p>
          )}
          {sources.length > 0 && (
            <div className="mt-1.5 flex flex-wrap gap-1 text-[10px] uppercase tracking-wide text-muted-foreground">
              {skill.evidence.slice(0, 5).map((e, idx) => (
                <span
                  key={`${e.source_type}:${e.source_id}:${idx}`}
                  className="rounded-md border border-muted px-1.5 py-0.5"
                  title={e.snippet}
                >
                  {SOURCE_ABBREV[e.source_type] ?? e.source_type} · {e.source_label}
                </span>
              ))}
              {skill.evidence.length > 5 && (
                <span className="text-muted-foreground/70">+{skill.evidence.length - 5} more</span>
              )}
            </div>
          )}
        </div>
        <ConfidenceBar confidence={skill.confidence} />
      </div>
    </li>
  );
}

export function SkillEvidenceCard({
  report,
  isLoading,
  hasAnalysis,
}: {
  report: EvidenceReport | undefined;
  isLoading: boolean;
  hasAnalysis: boolean;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Target className="h-4 w-4 text-primary" />
          Evidence & gap analysis
        </CardTitle>
        <CardDescription className="text-xs">
          {report
            ? `${report.counts.strong} strong · ${report.counts.weak} weak · ${report.counts.missing} missing — sourced from ${report.portfolio_count} portfolios, ${report.resume_count} resumes, ${report.repository_count} repos`
            : "Per-skill evidence pulled from your portfolios, resume, and scanned repositories."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!hasAnalysis ? (
          <div className="text-sm text-muted-foreground">
            Run <span className="font-medium text-foreground">Analyze job</span> first — the gap
            check needs the extracted skill list.
          </div>
        ) : isLoading || !report ? (
          <div className="text-sm text-muted-foreground">Building evidence report…</div>
        ) : (
          STATUS_ORDER.map((status) => {
            const rows = report.skills.filter((s) => s.status === status);
            if (!rows.length) return null;
            const meta = STATUS_META[status];
            const Icon = meta.icon;
            return (
              <section key={status} className="space-y-2">
                <div className={cn("flex items-center gap-2 text-xs uppercase tracking-wide", meta.tone)}>
                  <Icon className="h-3.5 w-3.5" />
                  {meta.label} ({rows.length})
                </div>
                <ul className="space-y-2">
                  {rows.map((s) => (
                    <SkillRow key={s.name} skill={s} />
                  ))}
                </ul>
              </section>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}
