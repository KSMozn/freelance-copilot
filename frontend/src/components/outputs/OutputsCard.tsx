import {
  Award,
  Briefcase,
  Copy,
  FileText,
  GitBranch,
  Link as LinkIcon,
  Linkedin,
  Mail,
  MessageSquare,
  Plus,
  Sparkles,
  Trash2,
  User2,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import {
  OUTPUT_KIND_LABELS,
  type Citation,
  type EvidenceType,
  type Output,
  type OutputKind,
  useDeleteOutput,
  useGenerateOutput,
  useOutputsForJob,
} from "@/lib/outputs";
import { useAuthStore } from "@/stores/auth";

interface Props {
  jobId: string;
}

const KIND_ORDER: OutputKind[] = [
  "cover_letter",
  "upwork_proposal",
  "linkedin_message",
  "recruiter_reply",
  "consulting_proposal",
  "screening_answer",
  "resume_tailored",
];

const KIND_ICONS: Record<OutputKind, React.ComponentType<{ className?: string }>> = {
  cover_letter: FileText,
  upwork_proposal: Briefcase,
  linkedin_message: Linkedin,
  recruiter_reply: Mail,
  consulting_proposal: Sparkles,
  screening_answer: MessageSquare,
  resume_tailored: FileText,
};

const EVIDENCE_ICONS: Record<EvidenceType, React.ComponentType<{ className?: string }>> = {
  experience: User2,
  project: Briefcase,
  repository: GitBranch,
  certificate: Award,
  content_item: LinkIcon,
  skill: Sparkles,
};

export function OutputsCard({ jobId }: Props) {
  const activePersonaId = useAuthStore((s) => s.activePersonaId);
  const { data: outputs, isLoading } = useOutputsForJob(jobId);
  const generate = useGenerateOutput(jobId);
  const remove = useDeleteOutput(jobId);
  const [expanded, setExpanded] = useState<string | null>(null);

  function onGenerate(kind: OutputKind) {
    generate.mutate(
      { kind, personaId: activePersonaId },
      {
        onSuccess: (o) => {
          toast.success(`${OUTPUT_KIND_LABELS[kind]} generated`);
          setExpanded(o.id);
        },
        onError: (err: unknown) => {
          const detail = (
            err as { response?: { data?: { detail?: string } } }
          )?.response?.data?.detail;
          toast.error(detail ?? "Generation failed");
        },
      },
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          Generate output
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
            Phase F
          </span>
        </CardTitle>
        <CardDescription>
          One click to draft a tailored artifact. Every claim cites a graph
          node — switch personas in the topbar to re-tone the output.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {KIND_ORDER.map((kind) => {
            const Icon = KIND_ICONS[kind];
            const isPending =
              generate.isPending && generate.variables?.kind === kind;
            return (
              <Button
                key={kind}
                size="sm"
                variant="outline"
                onClick={() => onGenerate(kind)}
                disabled={generate.isPending}
              >
                <Icon className="h-4 w-4 mr-2" />
                {isPending ? "Generating…" : OUTPUT_KIND_LABELS[kind]}
                {!isPending && <Plus className="h-3 w-3 ml-1 opacity-50" />}
              </Button>
            );
          })}
        </div>

        {isLoading && (
          <p className="text-sm text-muted-foreground">Loading drafts…</p>
        )}

        {(outputs ?? []).length === 0 && !isLoading && (
          <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground text-center">
            No drafts yet. Pick a format above to generate one.
          </div>
        )}

        <div className="space-y-3">
          {(outputs ?? []).map((output) => (
            <OutputRow
              key={output.id}
              output={output}
              expanded={expanded === output.id}
              onToggle={() =>
                setExpanded((prev) => (prev === output.id ? null : output.id))
              }
              onDelete={() => {
                if (!confirm(`Delete this ${OUTPUT_KIND_LABELS[output.kind]}?`)) return;
                remove.mutate(output.id);
              }}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function OutputRow({
  output,
  expanded,
  onToggle,
  onDelete,
}: {
  output: Output;
  expanded: boolean;
  onToggle: () => void;
  onDelete: () => void;
}) {
  const Icon = KIND_ICONS[output.kind];
  const created = output.created_at ? new Date(output.created_at) : null;
  return (
    <div className="rounded-md border bg-muted/30">
      <button
        type="button"
        onClick={onToggle}
        className="w-full px-3 py-2 flex items-center gap-3 text-left hover:bg-muted/50"
      >
        <Icon className="h-4 w-4 text-primary shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">
            {output.title ?? OUTPUT_KIND_LABELS[output.kind]}
          </p>
          <p className="text-xs text-muted-foreground">
            {OUTPUT_KIND_LABELS[output.kind]}
            {created && ` · ${created.toLocaleString()}`}
            {output.citations.length > 0 &&
              ` · ${output.citations.length} citation${output.citations.length === 1 ? "" : "s"}`}
          </p>
        </div>
        <span className="text-xs text-muted-foreground">
          {expanded ? "Hide" : "Open"}
        </span>
      </button>
      {expanded && (
        <div className="px-3 pb-3 space-y-3 border-t pt-3">
          <Markdown text={output.content_markdown} />

          {output.citations.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">
                Evidence
              </p>
              <div className="flex flex-wrap gap-1.5">
                {output.citations.map((c, i) => (
                  <CitationChip key={`${c.evidence_id ?? c.evidence_label}-${i}`} c={c} />
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-1">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                navigator.clipboard.writeText(output.content_markdown);
                toast.success("Copied markdown");
              }}
            >
              <Copy className="h-3 w-3 mr-1" />
              Copy
            </Button>
            <Button size="sm" variant="ghost" className="text-destructive" onClick={onDelete}>
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

function CitationChip({ c }: { c: Citation }) {
  const Icon = EVIDENCE_ICONS[c.evidence_type] ?? Sparkles;
  return (
    <Badge
      variant="outline"
      className="text-[11px] gap-1 cursor-help"
      title={c.snippet ? `${c.claim} — "${c.snippet}"` : c.claim}
    >
      <Icon className="h-3 w-3" />
      {c.evidence_label}
    </Badge>
  );
}

// ---- minimal markdown renderer ------------------------------------------

function Markdown({ text }: { text: string }) {
  // Lightweight inline rendering — split paragraphs on blank lines, render
  // `##` as h3, `- ` as bullets, leave the rest as <p>. No external dep.
  const blocks = text.split(/\n{2,}/);
  return (
    <div className="space-y-3 text-sm leading-relaxed whitespace-pre-wrap">
      {blocks.map((block, i) => {
        const trimmed = block.trim();
        if (trimmed.startsWith("### ")) {
          return (
            <h4 key={i} className="text-sm font-semibold">
              {trimmed.slice(4)}
            </h4>
          );
        }
        if (trimmed.startsWith("## ")) {
          return (
            <h3 key={i} className="text-base font-semibold">
              {trimmed.slice(3)}
            </h3>
          );
        }
        if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          const items = trimmed.split(/\n(?=- |\* )/);
          return (
            <ul key={i} className="list-disc pl-5 space-y-1">
              {items.map((it, j) => (
                <li key={j}>{it.replace(/^[-*]\s+/, "")}</li>
              ))}
            </ul>
          );
        }
        return <p key={i}>{trimmed}</p>;
      })}
    </div>
  );
}
