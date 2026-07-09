import { AlertTriangle, CheckCircle2, HelpCircle, Sparkles } from "lucide-react";

import { Badge } from "@/shared/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { cn } from "@/shared/lib/utils";
import type { JobAnalysis, Severity } from "@/types/api";

function ChipList({ items, variant = "secondary" }: { items: string[]; variant?: "default" | "secondary" | "outline" }) {
  if (!items.length) return <span className="text-sm text-muted-foreground">—</span>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item) => (
        <Badge key={item} variant={variant}>
          {item}
        </Badge>
      ))}
    </div>
  );
}

const SEVERITY_STYLES: Record<Severity, string> = {
  low: "border-emerald-500/40 text-emerald-400",
  medium: "border-amber-500/40 text-amber-400",
  high: "border-rose-500/40 text-rose-400",
};

export function SummaryCard({ analysis }: { analysis: JobAnalysis }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Sparkles className="h-4 w-4 text-primary" />
          Summary
        </CardTitle>
        <CardDescription className="text-xs">
          {analysis.provider ? `${analysis.provider} · ${analysis.model ?? ""}` : "n/a"} · prompt {analysis.prompt_version ?? "?"}
        </CardDescription>
      </CardHeader>
      <CardContent className="text-sm leading-relaxed">{analysis.summary ?? "—"}</CardContent>
    </Card>
  );
}

export function ExtractionCard({ analysis }: { analysis: JobAnalysis }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">What the AI extracted</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <div>
          <div className="mb-1.5 text-xs uppercase tracking-wide text-muted-foreground">Required skills</div>
          <ChipList items={analysis.required_skills} />
        </div>
        {analysis.preferred_skills.length > 0 && (
          <div>
            <div className="mb-1.5 text-xs uppercase tracking-wide text-muted-foreground">Preferred skills</div>
            <ChipList items={analysis.preferred_skills} variant="outline" />
          </div>
        )}
        <div>
          <div className="mb-1.5 text-xs uppercase tracking-wide text-muted-foreground">Technologies</div>
          <ChipList items={analysis.technologies} variant="outline" />
        </div>
        <div className="grid grid-cols-2 gap-3 pt-1 md:grid-cols-4">
          <Field label="Business domain" value={analysis.business_domain} />
          <Field label="Seniority" value={analysis.seniority} />
          <Field label="Complexity" value={analysis.complexity} />
          <Field
            label="Effort (hrs)"
            value={
              analysis.estimated_hours_min != null && analysis.estimated_hours_max != null
                ? `${analysis.estimated_hours_min}–${analysis.estimated_hours_max}`
                : "—"
            }
          />
          <Field label="Budget assessment" value={analysis.budget_assessment} />
          <Field label="Risk level" value={analysis.risk_level} />
          <Field label="Client intent" value={analysis.client_intent} className="col-span-2" />
        </div>
        {analysis.expected_deliverables.length > 0 && (
          <div>
            <div className="mb-1.5 text-xs uppercase tracking-wide text-muted-foreground">Deliverables</div>
            <ul className="list-disc space-y-1 pl-5">
              {analysis.expected_deliverables.map((d) => (
                <li key={d}>{d}</li>
              ))}
            </ul>
          </div>
        )}
        {analysis.hidden_requirements.length > 0 && (
          <div>
            <div className="mb-1.5 text-xs uppercase tracking-wide text-muted-foreground">
              Hidden requirements
            </div>
            <ul className="list-disc space-y-1 pl-5">
              {analysis.hidden_requirements.map((d) => (
                <li key={d}>{d}</li>
              ))}
            </ul>
          </div>
        )}
        {analysis.communication_required && (
          <Field label="Communication" value={analysis.communication_required} />
        )}
      </CardContent>
    </Card>
  );
}

function Field({
  label,
  value,
  className,
}: {
  label: string;
  value: string | null | undefined;
  className?: string;
}) {
  return (
    <div className={className}>
      <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="text-sm">{value || "—"}</div>
    </div>
  );
}

export function RisksCard({ analysis }: { analysis: JobAnalysis }) {
  if (!analysis.risks.length) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <AlertTriangle className="h-4 w-4 text-amber-400" />
          Risks
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {analysis.risks.map((r, i) => (
          <div key={i} className="rounded-md border border-border/70 p-3">
            <div className="flex items-start justify-between gap-3">
              <div className="font-medium">{r.risk}</div>
              <span
                className={cn(
                  "rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-wider",
                  SEVERITY_STYLES[r.severity],
                )}
              >
                {r.severity}
              </span>
            </div>
            <div className="mt-1 text-muted-foreground">{r.mitigation}</div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export function FlagsCard({ analysis }: { analysis: JobAnalysis }) {
  if (!analysis.red_flags.length && !analysis.green_flags.length) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Flags</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-2">
        <div>
          <div className="mb-1.5 flex items-center gap-2 text-xs uppercase tracking-wide text-emerald-400">
            <CheckCircle2 className="h-3.5 w-3.5" /> Green flags
          </div>
          {analysis.green_flags.length === 0 ? (
            <div className="text-sm text-muted-foreground">—</div>
          ) : (
            <ul className="space-y-1 text-sm">
              {analysis.green_flags.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          )}
        </div>
        <div>
          <div className="mb-1.5 flex items-center gap-2 text-xs uppercase tracking-wide text-rose-400">
            <AlertTriangle className="h-3.5 w-3.5" /> Red flags
          </div>
          {analysis.red_flags.length === 0 ? (
            <div className="text-sm text-muted-foreground">—</div>
          ) : (
            <ul className="space-y-1 text-sm">
              {analysis.red_flags.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function QuestionsCard({ analysis }: { analysis: JobAnalysis }) {
  if (!analysis.questions_to_ask_client.length) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <HelpCircle className="h-4 w-4 text-primary" />
          Questions to ask the client
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="list-decimal space-y-1 pl-5 text-sm">
          {analysis.questions_to_ask_client.map((q) => (
            <li key={q}>{q}</li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
